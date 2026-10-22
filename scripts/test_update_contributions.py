import base64
import unittest
from urllib.parse import parse_qs, urlparse

from update_contributions import collect_pull_requests, managed_contents, publish, PullRequest, render


README = """Backend story: protect unique inventory.
### Merged contributions
<!-- OSS:MERGED:START -->
<!-- OSS:MERGED:END -->
### Incorporated upstream
Manual credit: https://github.com/example/instructor/pull/999
### Pending contributions
<!-- OSS:PENDING:START -->
<!-- OSS:PENDING:END -->
<!-- OSS:COUNTS:START -->
<!-- OSS:COUNTS:END -->
Contact and personal projects stay here.
"""
CONFIG = {"owner": "imharjot"}


def raw_pr(repository="example/library", number=1, state="open", merged_at=None,
           private=False, author="imharjot"):
    return {"number": number, "title": "Fix a real bug", "state": state, "merged_at": merged_at,
            "user": {"login": author}, "base": {"repo": {"private": private,
            "full_name": repository, "owner": {"login": repository.split("/")[0]}}}}


class Catalog:
    def __init__(self, prs, *, incomplete=False, total=None):
        self.prs = prs
        self.incomplete = incomplete
        self.total = len(prs) if total is None else total
        self.calls = []

    def request(self, path):
        self.calls.append(path)
        if path.startswith("search/issues?"):
            page = int(parse_qs(urlparse(path).query)["page"][0])
            items = [{"html_url": f'https://github.com/{p["base"]["repo"]["full_name"]}/pull/{p["number"]}'}
                     for p in self.prs[(page - 1) * 100:page * 100]]
            return {"total_count": self.total, "incomplete_results": self.incomplete, "items": items}
        for pr in self.prs:
            if path.casefold() == f'repos/{pr["base"]["repo"]["full_name"]}/pulls/{pr["number"]}'.casefold():
                return pr
        raise AssertionError("Unexpected endpoint: " + path)


class ContributionTests(unittest.TestCase):
    def test_merge_moves_pr_out_of_pending(self):
        before = render(README, [PullRequest("example/library", 1, "Fix", "open")], CONFIG)
        after = render(before, [PullRequest("example/library", 1, "Fix", "merged", "2026-10-22")], CONFIG)
        regions = managed_contents(after)
        self.assertIn("/pull/1", regions["MERGED"])
        self.assertNotIn("/pull/1", regions["PENDING"])
        self.assertIn("1 merged OSS PRs · 0 open", regions["COUNTS"])

    def test_closed_without_merge_is_not_a_merged_contribution(self):
        after = render(README, [PullRequest("example/library", 1, "Fix", "closed")], CONFIG)
        self.assertNotIn("/pull/1", after)
        self.assertIn("0 merged OSS PRs · 0 open", after)

    def test_reopened_pr_returns_to_pending(self):
        closed = render(README, [PullRequest("example/library", 1, "Fix", "closed")], CONFIG)
        reopened = render(closed, [PullRequest("example/library", 1, "Fix", "open")], CONFIG)
        self.assertIn("/pull/1", managed_contents(reopened)["PENDING"])

    def test_manual_text_and_upstream_credit_are_unchanged(self):
        updated = render(README, [PullRequest("example/library", 1, "Fix", "open")], CONFIG)
        def without_generated(text):
            for name, content in managed_contents(text).items():
                start, end = f"<!-- OSS:{name}:START -->", f"<!-- OSS:{name}:END -->"
                first, last = text.index(start) + len(start), text.index(end)
                text = text[:first] + text[last:]
            return text
        self.assertEqual(without_generated(updated), without_generated(README))
        self.assertNotIn("999", managed_contents(updated)["MERGED"])

    def test_identical_data_produces_no_change(self):
        prs = [PullRequest("example/library", 1, "Fix", "open")]
        once = render(README, prs, CONFIG)
        self.assertEqual(render(once, prs, CONFIG), once)

    def test_missing_duplicate_reversed_or_overlapping_markers_fail(self):
        variants = [README.replace("<!-- OSS:MERGED:END -->", ""),
                    README + "<!-- OSS:PENDING:START -->",
                    README.replace("<!-- OSS:MERGED:START -->", "TEMP")
                          .replace("<!-- OSS:MERGED:END -->", "<!-- OSS:MERGED:START -->")
                          .replace("TEMP", "<!-- OSS:MERGED:END -->"),
                    README.replace("<!-- OSS:MERGED:END -->", "") + "<!-- OSS:MERGED:END -->"]
        for text in variants:
            with self.subTest(text=text), self.assertRaises(ValueError):
                render(text, [], CONFIG)

    def test_untrusted_titles_cannot_add_html_links_or_table_rows(self):
        title = '<img src=x> [click](https://evil.example)\n| another row'
        updated = render(README, [PullRequest("example/library", 1, title, "open")], CONFIG)
        self.assertNotIn("<img", updated)
        self.assertIn("&lt;img src=x&gt;", updated)
        self.assertIn(r"\[click\]\(https://evil.example\)", updated)
        self.assertIn(r"\| another row", updated)

    def test_all_search_pages_are_fetched_and_pr_state_is_authoritative(self):
        api = Catalog([raw_pr(number=n, state="closed", merged_at="2026-10-22") for n in range(1, 102)])
        prs = collect_pull_requests(api, "imharjot", README)
        self.assertEqual(len(prs), 101)
        self.assertTrue(all(pr.state == "merged" for pr in prs))
        self.assertEqual(len([p for p in api.calls if p.startswith("search/issues?")]), 2)
        self.assertTrue(any("pulls/101" in p for p in api.calls))

    def test_known_pr_is_checked_even_if_temporarily_missing_from_search(self):
        readme = render(README, [PullRequest("example/library", 1, "Fix", "open")], CONFIG)
        class MissingFromSearch(Catalog):
            def request(self, path):
                if path.startswith("search/issues?"):
                    return {"total_count": 0, "incomplete_results": False, "items": []}
                return super().request(path)
        api = MissingFromSearch([raw_pr(state="closed", merged_at="2026-10-22")])
        prs = collect_pull_requests(api, "imharjot", readme)
        self.assertEqual(prs[0].state, "merged")
        self.assertNotIn("pulls/999", " ".join(api.calls))

    def test_full_final_search_page_does_not_request_a_page_past_the_limit(self):
        api = Catalog([raw_pr(number=n) for n in range(1, 1001)])
        self.assertEqual(len(collect_pull_requests(api, "imharjot", README)), 1000)
        searches = [p for p in api.calls if p.startswith("search/issues?")]
        self.assertEqual(len(searches), 10)

    def test_personal_and_private_repositories_are_excluded(self):
        api = Catalog([raw_pr("imharjot/project"), raw_pr("example/private", private=True), raw_pr()])
        prs = collect_pull_requests(api, "imharjot", README)
        self.assertEqual([p.repository for p in prs], ["example/library"])

    def test_case_differences_do_not_double_count_existing_links(self):
        readme = render(README, [PullRequest("Example/Library", 1, "Fix", "open")], CONFIG)
        prs = collect_pull_requests(Catalog([raw_pr()]), "imharjot", readme)
        self.assertEqual(len(prs), 1)

    def test_incomplete_truncated_or_wrong_author_data_aborts(self):
        cases = [Catalog([], incomplete=True), Catalog([], total=1001),
                 Catalog([raw_pr()], total=2), Catalog([raw_pr(author="someone-else")])]
        for api in cases:
            with self.subTest(api=api), self.assertRaises(ValueError):
                collect_pull_requests(api, "imharjot", README)

    def test_failed_api_fetch_aborts_instead_of_emptying_lists(self):
        class Broken(Catalog):
            def request(self, path):
                if path.startswith("repos/"):
                    raise OSError("GitHub is temporarily unavailable")
                return super().request(path)
        with self.assertRaises(OSError):
            collect_pull_requests(Broken([raw_pr()]), "imharjot", README)

    def test_publish_uses_latest_manual_text_and_content_sha(self):
        current = README.replace("Backend story:", "A newer manual edit:")
        class Publisher:
            def __init__(self):
                self.writes = []
            def request(self, path, *, method="GET", data=None):
                if method == "GET":
                    return {"sha": "latest-sha", "content": base64.b64encode(current.encode()).decode()}
                self.writes.append(data)
                return {"commit": {"html_url": "https://github.com/imharjot/imharjot/commit/example"}}
        api = Publisher()
        self.assertTrue(publish(api, "imharjot/imharjot", [], CONFIG))
        self.assertEqual(api.writes[0]["sha"], "latest-sha")
        self.assertIn("A newer manual edit:", base64.b64decode(api.writes[0]["content"]).decode())

    def test_publish_skips_noop_commit(self):
        current = render(README, [], CONFIG)
        class Noop:
            def request(self, path, *, method="GET", data=None):
                self.assert_get(method)
                return {"sha": "unchanged", "content": base64.b64encode(current.encode()).decode()}
            def assert_get(self, method):
                if method != "GET":
                    raise AssertionError("No update should be sent")
        self.assertFalse(publish(Noop(), "imharjot/imharjot", [], CONFIG))


if __name__ == "__main__":
    unittest.main()
