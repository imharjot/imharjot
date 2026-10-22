"""Refresh public OSS PRs without changing the hand-written profile sections."""

from __future__ import annotations

import argparse
import base64
from dataclasses import dataclass
import html
import json
import os
from pathlib import Path
import re
import sys
import time
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent.parent
BLOCKS = ("MERGED", "PENDING", "COUNTS")
PR_URL = re.compile(r"https://github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)/pull/([1-9][0-9]*)\b")


class GitHub:
    def __init__(self, token):
        self.token = token

    def request(self, path, *, method="GET", data=None):
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "imharjot-profile-contributions",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        if data is not None:
            headers["Content-Type"] = "application/json"
        request = Request(
            "https://api.github.com/" + path,
            data=json.dumps(data).encode() if data is not None else None,
            headers=headers,
            method=method,
        )
        for attempt in range(3):
            try:
                with urlopen(request, timeout=30) as response:
                    return json.load(response)
            except HTTPError as error:
                # Only retry reads: an ambiguous write must not create duplicate commits.
                if method != "GET" or error.code not in (429, 500, 502, 503, 504) or attempt == 2:
                    raise
                error.close()
                time.sleep(2 ** attempt)


@dataclass(frozen=True)
class PullRequest:
    repository: str
    number: int
    title: str
    state: str
    merged_at: str | None = None

    @property
    def url(self):
        return f"https://github.com/{self.repository}/pull/{self.number}"


def block_bounds(readme, name):
    start = f"<!-- OSS:{name}:START -->"
    end = f"<!-- OSS:{name}:END -->"
    if readme.count(start) != 1 or readme.count(end) != 1:
        raise ValueError(f"Expected exactly one pair of {name} markers; README left unchanged")
    first, last = readme.index(start) + len(start), readme.index(end)
    if first > last:
        raise ValueError(f"Reversed {name} markers; README left unchanged")
    return first, last


def managed_contents(readme):
    bounds = [block_bounds(readme, name) for name in BLOCKS]
    ordered = sorted(bounds)
    if any(left[1] >= right[0] for left, right in zip(ordered, ordered[1:])):
        raise ValueError("Overlapping contribution markers; README left unchanged")
    return {name: readme[first:last] for name, (first, last) in zip(BLOCKS, bounds)}


def collect_pull_requests(api, owner, readme):
    # Keep known PRs even when the search index briefly omits an existing result.
    sections = managed_contents(readme)
    refs = {match.groups() for value in sections.values() for match in PR_URL.finditer(value)}
    page = 1
    discovered = set()
    while True:
        query = urlencode({
            "q": f"author:{owner} is:pr is:public -user:{owner}",
            "per_page": 100, "page": page, "sort": "created", "order": "asc",
        })
        result = api.request("search/issues?" + query)
        if result.get("incomplete_results") or result["total_count"] > 1000:
            raise ValueError("GitHub search is incomplete or exceeds 1,000 results; README left unchanged")
        items = result["items"]
        for item in items:
            match = PR_URL.fullmatch(item["html_url"])
            if not match:
                raise ValueError("Unexpected PR URL in search results; README left unchanged")
            refs.add(match.groups())
            discovered.add(match.groups())
        if len(items) < 100 or len(discovered) >= result["total_count"]:
            break
        page += 1
    if len(discovered) != result["total_count"]:
        raise ValueError("GitHub search pagination changed during the run; README left unchanged")

    prs = []
    seen = set()
    for repository, number in sorted(refs):
        if repository.split("/")[0].casefold() == owner.casefold():
            continue
        # Search supplies the catalog; the PR endpoint supplies authoritative state.
        # A stale search index must not keep a merged PR in the pending list.
        pr = api.request(f"repos/{repository}/pulls/{number}")
        repo = pr["base"]["repo"]
        if repo["private"] or repo["owner"]["login"].casefold() == owner.casefold():
            continue
        if pr["user"]["login"].casefold() != owner.casefold():
            raise ValueError("A contribution was not authored by the profile owner")
        identity = (repo["full_name"].casefold(), pr["number"])
        if identity in seen:
            continue
        seen.add(identity)
        state = "merged" if pr["merged_at"] else pr["state"]
        if state not in ("open", "closed", "merged"):
            raise ValueError("Unexpected pull-request state")
        prs.append(PullRequest(repo["full_name"], pr["number"], pr["title"], state, pr["merged_at"]))
    return prs


def markdown_text(value):
    value = html.escape(" ".join(value.split()), quote=False)
    return re.sub(r"([\\`*_{}\[\]()|])", r"\\\1", value)


def render(readme, prs, config):
    managed_contents(readme)
    aliases = config.get("repositories", {})
    descriptions = config.get("descriptions", {})

    def project(pr):
        return markdown_text(aliases.get(pr.repository, pr.repository))

    def description(pr):
        return markdown_text(descriptions.get(pr.url, pr.title))

    merged = sorted((pr for pr in prs if pr.state == "merged"),
                    key=lambda pr: (pr.merged_at or "", pr.url), reverse=True)
    pending = sorted((pr for pr in prs if pr.state == "open"),
                     key=lambda pr: (project(pr).casefold(), -pr.number))
    merged_text = "\n".join(
        f"- **{project(pr)}** — [{description(pr)}]({pr.url})." for pr in merged
    ) or "No merged public OSS pull requests yet."
    if pending:
        pending_text = "\n".join([
            "<details>", "<summary>View the open pull requests</summary>", "",
            "| Project | Contribution |", "| --- | --- |",
            *[f"| {project(pr)} | [{description(pr)}]({pr.url}) |" for pr in pending],
            "", "</details>",
        ])
    else:
        pending_text = "No open public OSS pull requests at the moment."
    contents = {
        "MERGED": merged_text,
        "PENDING": pending_text,
        "COUNTS": f"*{len(merged)} merged OSS PRs · {len(pending)} open. "
                  "Lists refresh hourly from GitHub; personal project PRs are excluded.*",
    }
    updated = readme
    for name, text in contents.items():
        first, last = block_bounds(updated, name)
        updated = updated[:first] + "\n\n" + text + "\n\n" + updated[last:]
    return updated


def publish(api, repository, prs, config):
    # Fetch the latest text immediately before publishing. The content SHA protects
    # against overwriting a simultaneous manual edit, including the backend story.
    current = api.request(f"repos/{repository}/contents/README.md?ref=main")
    original = base64.b64decode(current["content"], validate=False).decode()
    updated = render(original, prs, config)
    if updated == original:
        print("Contribution lists are current; no commit needed.")
        return False
    result = api.request(f"repos/{repository}/contents/README.md", method="PUT", data={
        "message": "docs: refresh open-source contribution status",
        "content": base64.b64encode(updated.encode()).decode(),
        "sha": current["sha"], "branch": "main",
    })
    print("Updated contribution lists:", result["commit"]["html_url"])
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--write", action="store_true", help="Update the local README")
    modes.add_argument("--check", action="store_true", help="Exit nonzero if a refresh is needed")
    modes.add_argument("--publish", action="store_true", help="Publish with a SHA-protected GitHub API write")
    args = parser.parse_args()
    config = json.loads((ROOT / "contributions.json").read_text())
    owner = config["owner"]
    repository = f"{owner}/{owner}"
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if args.publish:
        if not token or os.environ.get("GITHUB_REPOSITORY", "").casefold() != repository.casefold():
            raise ValueError("Publishing requires a token and the matching profile repository context")
    api = GitHub(token)
    readme = (ROOT / "README.md").read_text()
    prs = collect_pull_requests(api, owner, readme)
    print(f"Checked {len(prs)} public OSS PRs: "
          f"{sum(pr.state == 'merged' for pr in prs)} merged, "
          f"{sum(pr.state == 'open' for pr in prs)} open.")
    if args.publish:
        publish(api, repository, prs, config)
    else:
        updated = render(readme, prs, config)
        if args.check:
            return int(updated != readme)
        if updated != readme:
            temporary = ROOT / ".README.md.tmp"
            temporary.write_text(updated)
            temporary.replace(ROOT / "README.md")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError) as error:
        print(f"Contribution refresh failed: {error}", file=sys.stderr)
        sys.exit(1)
