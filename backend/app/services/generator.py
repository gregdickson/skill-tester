import logging

from app.integrations.openrouter import OpenRouterClient

logger = logging.getLogger(__name__)


class Generator:
    """Generates outputs (skill.md, etc.) from trained weights."""

    def __init__(self, llm: OpenRouterClient):
        self.llm = llm

    async def generate(
        self,
        goal: str,
        components: list[dict],
        weights: dict[str, float],
        how_it_works: str | None = None,
        template_prompt: str | None = None,
    ) -> str:
        """Generate a skill.md using current trained weights.

        Args:
            goal: The network's ultimate end goal.
            components: List of dicts with keys: id, name, description, priority.
            weights: Dict mapping component id to current weight value.
            how_it_works: Optional master instruction for generation.
            template_prompt: Optional custom prompt template.
        """
        comp_instructions = []
        for c in sorted(components, key=lambda x: weights.get(str(x["id"]), 0.5), reverse=True):
            w = weights.get(str(c["id"]), 0.5)
            emphasis = self._weight_to_emphasis(w)
            comp_instructions.append(
                f"- {c['name']} (weight: {w:.2f}, emphasis: {emphasis}): {c['description']}"
            )

        comp_text = "\n".join(comp_instructions)

        if template_prompt:
            user_prompt = template_prompt.replace("{goal}", goal).replace(
                "{components}", comp_text
            )
        else:
            user_prompt = (
                f"Generate a comprehensive, production-ready skill.md file.\n\n"
                f"GOAL: {goal}\n\n"
                f"The skill should cover these components with depth proportional to their weight. "
                f"Higher-weighted components get more detailed coverage, examples, and nuance. "
                f"Lower-weighted components get brief mentions.\n\n"
                f"COMPONENTS (ordered by importance):\n{comp_text}\n\n"
                f"Output the complete skill.md content, ready to use. Use markdown formatting. "
                f"Make it thorough, actionable, and expertly crafted."
            )

        system = how_it_works or (
            "You are an expert skill file author. You create comprehensive, "
            "production-ready skill files that serve as master instructions for AI agents. "
            "Your outputs are precise, actionable, and structured for maximum effectiveness."
        )

        return await self.llm.chat_with_system(
            system=system,
            user=user_prompt,
            temperature=0.7,
            max_tokens=8000,
        )

    @staticmethod
    def _weight_to_emphasis(weight: float) -> str:
        if weight > 0.8:
            return "CRITICAL"
        if weight > 0.6:
            return "HIGH"
        if weight > 0.4:
            return "MODERATE"
        if weight > 0.2:
            return "LIGHT"
        return "MINIMAL"
