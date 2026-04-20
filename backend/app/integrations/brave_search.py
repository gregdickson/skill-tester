import httpx
import trafilatura


class BraveSearchClient:
    BASE_URL = "https://api.search.brave.com/res/v1/web/search"

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def search(self, query: str, count: int = 5) -> list[dict]:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                self.BASE_URL,
                headers={
                    "X-Subscription-Token": self.api_key,
                    "Accept": "application/json",
                },
                params={"q": query, "count": count, "extra_snippets": "true"},
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("web", {}).get("results", [])

    async def search_and_extract(
        self, query: str, max_pages: int = 3
    ) -> list[dict]:
        results = await self.search(query)
        extracted = []

        async with httpx.AsyncClient(
            timeout=10.0,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (compatible; SkillOptimiser/1.0)"},
        ) as client:
            for result in results[:max_pages]:
                entry = {
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "snippet": result.get("description", ""),
                    "extra_snippets": result.get("extra_snippets", []),
                    "content": "",
                }
                try:
                    page = await client.get(result["url"])
                    if page.status_code == 200:
                        content = trafilatura.extract(page.text) or ""
                        entry["content"] = content[:5000]
                except Exception:
                    pass
                extracted.append(entry)

        return extracted
