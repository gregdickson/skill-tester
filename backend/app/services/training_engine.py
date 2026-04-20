import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.engine.value import Value
from app.engine.optimizer import SGD
from app.models.component import Component
from app.models.network import Network
from app.models.training import TrainingRun, Evaluation
from app.models.activity import ActivityLog
from app.services.evaluator import Evaluator
from app.services.generator import Generator
from app.services.research_agent import ResearchAgent

logger = logging.getLogger(__name__)

# Default network config values
DEFAULT_CONFIG = {
    "learning_rate": 0.01,
    "research_depth": 0,
    "components_per_step": 5,
    "full_regen_frequency": 10,
    "priority_multipliers": {
        "critical": 2.0,
        "high": 1.5,
        "medium": 1.0,
        "low": 0.5,
    },
}

# Active training tasks keyed by network_id
_active_tasks: dict[str, asyncio.Task] = {}


class TrainingEngine:
    """Core training loop with micrograd Value weights and finite-difference gradients.

    Optimised approach:
    - Generate output once (cached), re-evaluate with nudged weights
    - Batch scoring: all selected components in one LLM call
    - Round-robin: only nudge N components per step
    - Full regeneration checkpoint every M steps
    """

    def __init__(
        self,
        network: Network,
        components: list[Component],
        evaluator: Evaluator,
        generator: Generator,
        research_agent: ResearchAgent | None,
        db_factory,
        ws_broadcast,
    ):
        self.network = network
        self.components = components
        self.evaluator = evaluator
        self.generator = generator
        self.research_agent = research_agent
        self.db_factory = db_factory
        self.ws_broadcast = ws_broadcast

        config = {**DEFAULT_CONFIG, **(network.network_config or {})}
        self.learning_rate = config["learning_rate"]
        self.components_per_step = config["components_per_step"]
        self.full_regen_frequency = config["full_regen_frequency"]
        self.research_depth = config["research_depth"]
        self.priority_multipliers = config["priority_multipliers"]

        # Micrograd weights
        self.weights: dict[str, Value] = {
            str(c.id): Value(c.weight, label=c.name) for c in components
        }
        self.optimizer = SGD(list(self.weights.values()), lr=self.learning_rate)

        self.step_index = 0
        self.cached_output: str | None = None
        self._paused = False

    def _comp_dicts(self) -> list[dict]:
        return [
            {"id": str(c.id), "name": c.name, "description": c.description or "", "priority": c.priority}
            for c in self.components
        ]

    def _weights_dict(self) -> dict[str, float]:
        return {cid: v.data for cid, v in self.weights.items()}

    def _select_components(self) -> list[Component]:
        n = min(self.components_per_step, len(self.components))
        start = self.step_index % len(self.components)
        selected = []
        for i in range(n):
            idx = (start + i) % len(self.components)
            selected.append(self.components[idx])
        self.step_index += n
        return selected

    def compute_loss(self, scores: dict[str, float]) -> float:
        total = 0.0
        for c in self.components:
            cid = str(c.id)
            if cid in scores:
                priority_w = self.priority_multipliers.get(c.priority, 1.0)
                total += priority_w * (1.0 - scores[cid]) ** 2
        return total

    async def _log_activity(self, db: AsyncSession, event_type: str, message: str, detail: dict | None = None):
        log = ActivityLog(
            network_id=self.network.id,
            event_type=event_type,
            message=message,
            detail=detail or {},
        )
        db.add(log)
        await db.flush()

        if self.ws_broadcast:
            await self.ws_broadcast(str(self.network.id), {
                "type": f"training.{event_type}",
                "data": {"message": message, **(detail or {})},
            })

    async def run_training(self, run: TrainingRun, total_steps: int):
        """Execute the full training loop."""
        started = time.time()

        async with self.db_factory() as db:
            await self._log_activity(db, "training_step", f"Training started: {total_steps} steps planned")
            await db.commit()

        try:
            for step in range(1, total_steps + 1):
                if self._paused:
                    async with self.db_factory() as db:
                        run.status = "paused"
                        db.add(run)
                        await self._log_activity(db, "training_step", f"Training paused at step {step}")
                        await db.commit()
                    return

                step_result = await self._training_step(step, run)

                async with self.db_factory() as db:
                    # Update training run
                    run.total_steps = step
                    run.loss_history = [*run.loss_history, {"step": step, "loss": round(step_result["loss"], 4)}]
                    run.loss_end = step_result["loss"]
                    if step == 1:
                        run.loss_start = step_result["loss"]
                    db.add(run)

                    # Update component weights in DB
                    for c in self.components:
                        cid = str(c.id)
                        w = self.weights[cid]
                        score = step_result.get("scores", {}).get(cid, c.score_pct)
                        status = "strong" if score >= 0.7 else "developing" if score >= 0.4 else "weak"
                        await db.execute(
                            update(Component)
                            .where(Component.id == c.id)
                            .values(weight=w.data, score_pct=score, status=status)
                        )

                    # Update network
                    await db.execute(
                        update(Network)
                        .where(Network.id == self.network.id)
                        .values(
                            current_loss=step_result["loss"],
                            total_steps=Network.total_steps + 1,
                            status="training",
                        )
                    )

                    await self._log_activity(
                        db, "training_step",
                        f"Step {step}/{total_steps} — loss: {step_result['loss']:.4f}",
                        {"step": step, "loss": step_result["loss"], "components": step_result.get("trained", [])},
                    )
                    await db.commit()

            # Training complete
            elapsed = int(time.time() - started)
            async with self.db_factory() as db:
                run.status = "complete"
                run.completed_at = datetime.now(timezone.utc)
                run.duration_seconds = elapsed

                # Compute readiness
                weights_dict = self._weights_dict()
                all_comp_dicts = self._comp_dicts()
                final_scores = await self.evaluator.batch_score(
                    self.cached_output or "", all_comp_dicts, weights_dict
                )
                strong = sum(1 for s in final_scores.values() if s >= 0.7)
                readiness = (strong / len(self.components)) * 100 if self.components else 0

                run.improvements = {
                    "strong": strong,
                    "developing": sum(1 for s in final_scores.values() if 0.4 <= s < 0.7),
                    "weak": sum(1 for s in final_scores.values() if s < 0.4),
                }
                db.add(run)

                await db.execute(
                    update(Network)
                    .where(Network.id == self.network.id)
                    .values(status="converged" if readiness >= 80 else "training", readiness_pct=readiness)
                )

                await self._log_activity(
                    db, "training_step",
                    f"Training complete — {total_steps} steps, final loss: {run.loss_end:.4f}, readiness: {readiness:.0f}%",
                    {"final_loss": run.loss_end, "readiness": readiness, "duration": elapsed},
                )
                await db.commit()

        except Exception as e:
            logger.exception("Training failed")
            async with self.db_factory() as db:
                run.status = "failed"
                db.add(run)
                await self._log_activity(db, "error", f"Training failed: {str(e)}")
                await db.commit()
            raise

    async def _training_step(self, step_number: int, run: TrainingRun) -> dict:
        """One optimised training step."""
        selected = self._select_components()
        weights_dict = self._weights_dict()
        all_comp_dicts = self._comp_dicts()

        # Generate or reuse cached output
        if step_number == 1 or step_number % self.full_regen_frequency == 0:
            self.cached_output = await self.generator.generate(
                goal=self.network.ultimate_end_goal,
                components=all_comp_dicts,
                weights=weights_dict,
                how_it_works=self.network.how_it_works,
            )

        output = self.cached_output

        # Optional research for selected components
        if self.research_agent and self.research_depth > 0:
            for c in selected:
                notes = await self.research_agent.research_component(
                    c.name, self.network.ultimate_end_goal, depth=self.research_depth
                )
                c.research_notes = notes

        # Baseline batch score
        baseline_scores = await self.evaluator.batch_score(
            output, all_comp_dicts, weights_dict
        )
        baseline_loss = self.compute_loss(baseline_scores)

        # Nudge test each selected component
        self.optimizer.zero_grad()
        h = self.learning_rate

        for comp in selected:
            cid = str(comp.id)
            weight = self.weights[cid]
            original = weight.data

            # Nudge UP
            weight.data = min(1.0, original + h)
            nudged_weights_up = self._weights_dict()
            score_up = await self.evaluator.score_with_nudge(
                output,
                {"name": comp.name, "description": comp.description or "", "priority": comp.priority},
                weight.data,
                all_comp_dicts,
            )
            loss_up = self.priority_multipliers.get(comp.priority, 1.0) * (1.0 - score_up) ** 2

            # Nudge DOWN
            weight.data = max(0.0, original - h)
            score_down = await self.evaluator.score_with_nudge(
                output,
                {"name": comp.name, "description": comp.description or "", "priority": comp.priority},
                weight.data,
                all_comp_dicts,
            )
            loss_down = self.priority_multipliers.get(comp.priority, 1.0) * (1.0 - score_down) ** 2

            # Restore and compute gradient
            weight.data = original
            weight.grad = (loss_up - loss_down) / (2 * h) if h > 0 else 0.0

            # Record evaluations
            async with self.db_factory() as db:
                for direction, score in [("baseline", baseline_scores.get(cid, 0.5)),
                                          ("up", score_up), ("down", score_down)]:
                    ev = Evaluation(
                        training_run_id=run.id,
                        component_id=comp.id,
                        step_number=step_number,
                        nudge_direction=direction,
                        nudge_delta=h if direction != "baseline" else None,
                        score_before=baseline_scores.get(cid, 0.5),
                        score_after=score,
                    )
                    db.add(ev)

                await self._log_activity(
                    db, "weight_adjusted",
                    f"{comp.name}: grad={weight.grad:.4f}",
                    {"component": comp.name, "gradient": weight.grad, "weight": original},
                )
                await db.commit()

        # SGD update
        updates = self.optimizer.step()

        # Broadcast weight changes
        if self.ws_broadcast:
            for label, u in updates.items():
                if u["before"] != u["after"]:
                    await self.ws_broadcast(str(self.network.id), {
                        "type": "training.weight",
                        "data": {"component": label, **u},
                    })

        return {
            "loss": baseline_loss,
            "scores": baseline_scores,
            "trained": [c.name for c in selected],
            "updates": updates,
        }

    def pause(self):
        self._paused = True

    def resume(self):
        self._paused = False


def get_active_task(network_id: str) -> asyncio.Task | None:
    return _active_tasks.get(network_id)


def set_active_task(network_id: str, task: asyncio.Task | None):
    if task is None:
        _active_tasks.pop(network_id, None)
    else:
        _active_tasks[network_id] = task
