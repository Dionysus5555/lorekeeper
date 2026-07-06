from __future__ import annotations

import re
from typing import Any

import aiohttp


class GitHubProvider:
    """GitHub knowledge provider."""

    API_BASE = "https://api.github.com"

    def __init__(
        self,
        session: aiohttp.ClientSession,
        user_agent: str = "Lorekeeper Home Assistant Integration",
    ) -> None:
        self.session = session
        self.user_agent = user_agent

    async def search(self, query: str, limit: int = 5) -> dict[str, Any]:
        """Search GitHub repositories."""
        url = f"{self.API_BASE}/search/repositories"

        data = await self._get_json(
            url,
            params={
                "q": query,
                "sort": "stars",
                "order": "desc",
                "per_page": limit,
            },
        )

        results = []

        for repo in data.get("items", []):
            results.append(
                {
                    "title": repo.get("full_name"),
                    "description": repo.get("description"),
                    "url": repo.get("html_url"),
                    "stars": repo.get("stargazers_count"),
                    "language": repo.get("language"),
                }
            )

        return {
            "found": bool(results),
            "provider": "github",
            "query": query,
            "results": results,
        }

    async def lookup(self, query: str) -> dict[str, Any]:
        """Look up a GitHub repository or GitHub-related query."""
        owner_repo = self._extract_owner_repo(query)

        if owner_repo:
            owner, repo = owner_repo
            return await self._repo_summary(owner, repo, query)

        search = await self.search(query, limit=1)

        if not search["found"]:
            return {
                "found": False,
                "provider": "github",
                "query": query,
                "title": None,
                "summary": None,
                "speech": None,
                "context": None,
                "url": None,
                "image": None,
                "error": "no_results",
            }

        full_name = search["results"][0]["title"]
        owner, repo = full_name.split("/", 1)
        return await self._repo_summary(owner, repo, query)

    async def summary(self, title: str) -> dict[str, Any]:
        """Summarise a GitHub repository by owner/repo."""
        owner_repo = self._extract_owner_repo(title)

        if not owner_repo and "/" in title:
            owner, repo = title.split("/", 1)
            return await self._repo_summary(owner.strip(), repo.strip(), title)

        if owner_repo:
            owner, repo = owner_repo
            return await self._repo_summary(owner, repo, title)

        return await self.lookup(title)

    async def _repo_summary(
        self,
        owner: str,
        repo: str,
        query: str | None = None,
    ) -> dict[str, Any]:
        """Return a repository summary."""
        repo_url = f"{self.API_BASE}/repos/{owner}/{repo}"

        try:
            repo_data = await self._get_json(repo_url)
        except aiohttp.ClientResponseError as err:
            if err.status == 404:
                return {
                    "found": False,
                    "provider": "github",
                    "query": query,
                    "title": f"{owner}/{repo}",
                    "summary": None,
                    "speech": None,
                    "context": None,
                    "url": None,
                    "image": None,
                    "error": "not_found",
                }
            raise

        readme_text = await self._get_readme(owner, repo)
        release_data = await self._get_latest_release(owner, repo)

        full_name = repo_data.get("full_name", f"{owner}/{repo}")
        description = repo_data.get("description")
        html_url = repo_data.get("html_url")

        summary_parts = []

        if description:
            summary_parts.append(description)

        summary_parts.append(
            f"It has {repo_data.get('stargazers_count', 0)} stars, "
            f"{repo_data.get('forks_count', 0)} forks, "
            f"and is primarily written in {repo_data.get('language') or 'an unspecified language'}."
        )

        if release_data:
            summary_parts.append(
                f"The latest release is {release_data.get('tag_name')}."
            )

        if readme_text:
            summary_parts.append(f"README excerpt: {readme_text}")

        summary = " ".join(summary_parts)
        speech = self._make_speech(full_name, description, release_data)

        context = f"Source: GitHub. Repository {full_name}: {summary}"

        return {
            "found": True,
            "provider": "github",
            "query": query,
            "title": full_name,
            "summary": summary,
            "speech": speech,
            "context": context,
            "description": description,
            "url": html_url,
            "image": repo_data.get("owner", {}).get("avatar_url"),
            "stars": repo_data.get("stargazers_count"),
            "forks": repo_data.get("forks_count"),
            "language": repo_data.get("language"),
            "latest_release": release_data.get("tag_name") if release_data else None,
        }

    async def _get_readme(self, owner: str, repo: str) -> str | None:
        """Fetch a short README excerpt."""
        url = f"{self.API_BASE}/repos/{owner}/{repo}/readme"

        try:
            data = await self._get_json(
                url,
                headers={"Accept": "application/vnd.github.raw"},
                raw=True,
            )
        except aiohttp.ClientResponseError:
            return None

        text = self._clean_markdown(data)

        if len(text) > 500:
            text = text[:497].rsplit(" ", 1)[0] + "..."

        return text

    async def _get_latest_release(self, owner: str, repo: str) -> dict[str, Any] | None:
        """Fetch latest GitHub release."""
        url = f"{self.API_BASE}/repos/{owner}/{repo}/releases/latest"

        try:
            return await self._get_json(url)
        except aiohttp.ClientResponseError:
            return None

    def _extract_owner_repo(self, text: str) -> tuple[str, str] | None:
        """Extract owner/repo from text."""
        github_match = re.search(
            r"github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)",
            text,
        )

        if github_match:
            return github_match.group(1), github_match.group(2).removesuffix(".git")

        owner_repo_match = re.search(
            r"\b([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)\b",
            text,
        )

        if owner_repo_match:
            return owner_repo_match.group(1), owner_repo_match.group(2)

        return None

    def _make_speech(
        self,
        full_name: str,
        description: str | None,
        release_data: dict[str, Any] | None,
    ) -> str:
        """Create a Gaia-friendly spoken response."""
        if description:
            speech = f"{full_name} is a GitHub repository. {description}"
        else:
            speech = f"{full_name} is a GitHub repository."

        if release_data:
            speech += f" The latest release is {release_data.get('tag_name')}."

        return speech

    def _clean_markdown(self, text: str) -> str:
        """Clean markdown into plain text."""
        text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
        text = re.sub(r"`([^`]*)`", r"\1", text)
        text = re.sub(r"!\[.*?\]\(.*?\)", "", text)
        text = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", text)
        text = re.sub(r"[#>*_\-]+", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    async def _get_json(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        raw: bool = False,
    ) -> Any:
        """Fetch JSON or raw text from GitHub."""
        request_headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        if headers:
            request_headers.update(headers)

        async with self.session.get(
            url,
            params=params,
            headers=request_headers,
            timeout=aiohttp.ClientTimeout(total=15),
        ) as response:
            response.raise_for_status()

            if raw:
                return await response.text()

            return await response.json()
