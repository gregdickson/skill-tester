import json
import logging
from uuid import UUID

from app.integrations.openrouter import OpenRouterClient

logger = logging.getLogger(__name__)


class Evaluator:
    """LLM-as-judge for scoring outputs against component criteria.

    Supports batch scoring (multiple components in one call) to minimise
    API usage during training.
    """

    def __init__(self, llm: OpenRouterClient):
        self.llm = llm

    async def batch_score(
        self,
        output: str,
        components: list[dict],
        weights: dict[str, float],
    ) -> dict[str, float]:
        """Score the output on each component. Returns {component_id: score 0.0-1.0}.

        Args:
            output: The generated text to evaluate.
            components: List of dicts with keys: id, name, description, priority.
            weights: Dict mapping component id to current weight value.
        """
        comp_lines = []
        for c in components:
            w = weights.get(str(c["id"]), 0.5)
            comp_lines.append(
                f"- **{c['name']}** (weight: {w:.2f}, priority: {c['priority']}): {c['description']}"
            )

        comp_text = "\n".join(comp_lines)
        id_map = {c["name"]: str(c["id"]) for c in components}

        response = await self.llm.chat_with_system(
            system=(
                "You are an expert evaluator. You score outputs on specific quality dimensions. "
                "Be precise and consistent. A score of 1.0 means the component is perfectly "
                "executed. A score of 0.0 means it is completely absent or wrong. "
                "Higher-weighted components should have proportionally more depth and coverage."
            ),
            user=(
                f"Score the following output on each component listed below.\n\n"
                f"OUTPUT TO EVALUATE:\n{output[:6000]}\n\n"
                f"COMPONENTS TO SCORE:\n{comp_text}\n\n"
                f"For each component, assess how well the output addresses it given its weight. "
                f"Higher-weighted components need more depth.\n\n"
                f"Return ONLY a JSON object mapping component names to scores (0.0-1.0):\n"
                f'{{"component_name": score, ...}}'
            ),
            temperature=0.3,
            max_tokens=2000,
            response_format={"type": "json_object"},
        )

        try:
            raw_scores = json.loads(response)
            scores = {}
            for name, score in raw_scores.items():
                comp_id = id_map.get(name)
                if comp_id:
                    scores[comp_id] = max(0.0, min(1.0, float(score)))
            return scores
        except (json.JSONDecodeError, TypeError, ValueError) as e:
            logger.error(f"Failed to parse evaluation scores: {e}")
            return {str(c["id"]): 0.5 for c in components}

    async def score_with_nudge(
        self,
        output: str,
        component: dict,
        nudged_weight: float,
        context_components: list[dict],
    ) -> float:
        """Score a single component with an adjusted weight emphasis.

        Used during nudge testing — tells the evaluator to assess whether
        the output meets the adjusted emphasis level.
        """
        emphasis = (
            "CRITICAL — this should dominate the output" if nudged_weight > 0.8
            else "HIGH — prominent coverage expected" if nudged_weight > 0.6
            else "MODERATE — balanced coverage" if nudged_weight > 0.4
            else "LIGHT — mentioned but not emphasised" if nudged_weight > 0.2
            else "MINIMAL — barely present is acceptable"
        )

        response = await self.llm.chat_with_system(
            system=(
                "You are an expert evaluator. Score how well an output addresses a specific "
                "component at a given emphasis level. Be precise: 1.0 means perfect execution "
                "at the specified emphasis, 0.0 means completely wrong."
            ),
            user=(
                f"Does this output appropriately address the following component at the "
                f"specified emphasis level?\n\n"
                f"COMPONENT: {component['name']}\n"
                f"DESCRIPTION: {component['description']}\n"
                f"EXPECTED EMPHASIS: {emphasis} (weight: {nudged_weight:.2f})\n\n"
                f"OUTPUT:\n{output[:6000]}\n\n"
                f"Return ONLY a JSON object: {{\"score\": <0.0-1.0>, \"reasoning\": \"...\"}}"
            ),
            temperature=0.3,
            max_tokens=500,
            response_format={"type": "json_object"},
        )

        try:
            data = json.loads(response)
            return max(0.0, min(1.0, float(data.get("score", 0.5))))
        except (json.JSONDecodeError, TypeError, ValueError):
            return 0.5
