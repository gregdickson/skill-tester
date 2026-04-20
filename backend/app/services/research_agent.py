import json
import logging

from app.integrations.openrouter import OpenRouterClient
from app.integrations.brave_search import BraveSearchClient

logger = logging.getLogger(__name__)


class ResearchAgent:
    """Performs web research and uses LLM to synthesise findings.

    Used for:
    - Auto-populating network components from an end goal
    - Researching individual components during training evaluation
    """

    def __init__(self, llm: OpenRouterClient, search: BraveSearchClient):
        self.llm = llm
        self.search = search

    async def generate_search_queries(self, goal: str, count: int = 4) -> list[str]:
        response = await self.llm.chat_with_system(
            system="You generate targeted search queries for researching a topic.",
            user=(
                f"Generate {count} diverse search queries to thoroughly research "
                f"all the components needed to achieve this goal:\n\n{goal}\n\n"
                f"Return ONLY a JSON array of strings, no other text."
            ),
            temperature=0.5,
            max_tokens=500,
            response_format={"type": "json_object"},
        )
        try:
            data = json.loads(response)
            if isinstance(data, list):
                return data[:count]
            if isinstance(data, dict):
                for v in data.values():
                    if isinstance(v, list):
                        return v[:count]
        except (json.JSONDecodeError, TypeError):
            pass
        return [goal]

    async def research_goal(self, goal: str, research_depth: int = 3) -> list[dict]:
        """Research a goal and return extracted content from multiple sources."""
        queries = await self.generate_search_queries(goal, count=research_depth + 1)
        all_content = []

        for query in queries:
            try:
                results = await self.search.search_and_extract(query, max_pages=3)
                all_content.extend(results)
            except Exception as e:
                logger.warning(f"Search failed for query '{query}': {e}")

        return all_content

    async def decompose_into_components(
        self, goal: str, title: str, purpose: str | None, research_depth: int = 3
    ) -> list[dict]:
        """Research the goal and decompose it into weighted components."""
        research_content = await self.research_goal(goal, research_depth)

        research_summary = "\n\n".join(
            f"## {r['title']}\nURL: {r['url']}\n{r['content'][:2000] or r['snippet']}"
            for r in research_content
            if r.get("content") or r.get("snippet")
        )

        response = await self.llm.chat_with_system(
            system=(
                "You are an expert at decomposing complex goals into measurable components. "
                "Each component represents a distinct skill or quality dimension that can be "
                "independently weighted and evaluated."
            ),
            user=(
                f"Based on the following research, decompose this goal into 15-40 weighted components.\n\n"
                f"GOAL: {goal}\n"
                f"TITLE: {title}\n"
                f"PURPOSE: {purpose or 'Not specified'}\n\n"
                f"RESEARCH:\n{research_summary[:8000]}\n\n"
                f"For each component, provide:\n"
                f"- name: Short descriptive name\n"
                f"- description: What this component covers (2-3 sentences)\n"
                f"- priority: critical | high | medium | low\n"
                f"- initial_weight: 0.0 to 1.0 (how important this is)\n"
                f"- rationale: Why this component matters\n"
                f"- sub_components: Optional list of finer-grained items (strings)\n\n"
                f"Return as a JSON object with a 'components' array."
            ),
            temperature=0.6,
            max_tokens=8000,
            response_format={"type": "json_object"},
        )

        try:
            data = json.loads(response)
            components = data.get("components", data if isinstance(data, list) else [])
            return components
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"Failed to parse component decomposition: {e}")
            return []

    async def research_component(self, component_name: str, context: str, depth: int = 1) -> str:
        """Research a specific component for training evaluation context."""
        query = f"{component_name} best practices {context}"
        try:
            results = await self.search.search_and_extract(query, max_pages=depth)
            notes = "\n\n".join(
                f"**{r['title']}** ({r['url']})\n{r['content'][:1500] or r['snippet']}"
                for r in results
                if r.get("content") or r.get("snippet")
            )
            return notes or "No research findings."
        except Exception as e:
            logger.warning(f"Research failed for component '{component_name}': {e}")
            return "Research unavailable."
