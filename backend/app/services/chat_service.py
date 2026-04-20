import json
import logging
from uuid import UUID

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.openrouter import OpenRouterClient
from app.models.network import Network
from app.models.component import Component
from app.models.training import TrainingRun
from app.models.activity import ActivityLog

logger = logging.getLogger(__name__)


class ChatService:
    """Dual-mode chat interface for learn and command modes.

    Can read network state, modify config, and answer questions about
    training progress.
    """

    def __init__(self, llm: OpenRouterClient):
        self.llm = llm

    async def handle_message(
        self, network_id: UUID, mode: str, message: str, db: AsyncSession
    ) -> dict:
        network = await db.get(Network, network_id)
        if not network:
            return {"message": "Network not found.", "config_changed": False}

        components = (
            await db.execute(
                select(Component)
                .where(Component.network_id == network_id)
                .order_by(Component.sort_order)
            )
        ).scalars().all()

        recent_activity = (
            await db.execute(
                select(ActivityLog)
                .where(ActivityLog.network_id == network_id)
                .order_by(ActivityLog.created_at.desc())
                .limit(10)
            )
        ).scalars().all()

        latest_run = (
            await db.execute(
                select(TrainingRun)
                .where(TrainingRun.network_id == network_id)
                .order_by(TrainingRun.started_at.desc())
                .limit(1)
            )
        ).scalars().first()

        context = self._build_context(network, components, recent_activity, latest_run, mode)

        system_prompt = (
            f"You are the AI assistant for the MicroGrad Skill Optimiser. "
            f"You are in {mode.upper()} mode.\n\n"
            f"You have access to the current network state and can help the user "
            f"understand training progress, modify configuration, and answer questions.\n\n"
            f"CURRENT STATE:\n{context}\n\n"
            f"When the user asks to change configuration, respond with your message AND "
            f"include a JSON block at the end with the changes:\n"
            f"```config_change\n{{\"field\": \"value\"}}\n```\n\n"
            f"Available config fields for learn mode: learning_rate, research_depth, "
            f"components_per_step, full_regen_frequency, how_it_works, "
            f"evaluation_criteria (list), priority_multipliers (dict).\n"
            f"Available config fields for command mode: how_it_works, output_type."
        )

        response = await self.llm.chat_with_system(
            system=system_prompt,
            user=message,
            temperature=0.7,
            max_tokens=2000,
        )

        # Check for config changes in the response
        config_changed = False
        if "```config_change" in response:
            try:
                json_start = response.index("```config_change") + len("```config_change")
                json_end = response.index("```", json_start)
                changes = json.loads(response[json_start:json_end].strip())
                await self._apply_config_changes(network, changes, mode, db)
                config_changed = True
                response = response[:response.index("```config_change")].strip()
            except (ValueError, json.JSONDecodeError) as e:
                logger.warning(f"Failed to parse config change: {e}")

        return {
            "message": response,
            "config_changed": config_changed,
            "action_triggered": None,
        }

    def _build_context(
        self, network: Network, components: list[Component],
        activity: list[ActivityLog], run: TrainingRun | None, mode: str
    ) -> str:
        parts = [
            f"Network: {network.title}",
            f"Goal: {network.ultimate_end_goal}",
            f"Status: {network.status}",
            f"Mode: {network.mode}",
            f"Current Loss: {network.current_loss or 'N/A'}",
            f"Total Steps: {network.total_steps}",
            f"Readiness: {network.readiness_pct:.1f}%",
            "",
            "Components:",
        ]

        for c in components:
            parts.append(
                f"  - {c.name} (weight: {c.weight:.2f}, score: {c.score_pct:.0f}%, "
                f"priority: {c.priority}, status: {c.status})"
            )

        if run:
            parts.extend([
                "",
                f"Latest Training Run: v{run.version} — {run.status}",
                f"  Steps: {run.total_steps}, Loss: {run.loss_start} -> {run.loss_end}",
            ])

        config = network.learning_config if mode == "learn" else network.command_config
        if config:
            parts.extend(["", f"Config ({mode}):", json.dumps(config, indent=2)])

        if activity:
            parts.extend(["", "Recent Activity:"])
            for a in activity[:5]:
                parts.append(f"  [{a.created_at:%H:%M}] {a.message}")

        return "\n".join(parts)

    async def _apply_config_changes(
        self, network: Network, changes: dict, mode: str, db: AsyncSession
    ):
        config_field = "learning_config" if mode == "learn" else "command_config"
        current_config = getattr(network, config_field) or {}

        # Some fields go on the network directly
        direct_fields = {"how_it_works"}
        network_updates = {}
        config_updates = {}

        for key, value in changes.items():
            if key in direct_fields:
                network_updates[key] = value
            else:
                config_updates[key] = value

        if config_updates:
            new_config = {**current_config, **config_updates}
            network_updates[config_field] = new_config

        if network_updates:
            await db.execute(
                update(Network)
                .where(Network.id == network.id)
                .values(**network_updates)
            )
            await db.flush()
