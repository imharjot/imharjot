# Contribution list maintenance

The profile refreshes hourly at 17 minutes past the hour, and can also be refreshed
from **Actions → Update OSS contributions → Run workflow**. GitHub schedules can be
delayed, so this is a periodic refresh rather than an instant merge webhook.

The workflow discovers public PRs authored by `imharjot`, then reads each PR's
current status directly. A merged PR moves from pending to merged; a PR closed
without merging leaves pending; a reopened PR returns to pending. New public OSS
PRs are discovered automatically. Repositories owned by `imharjot` and private
repositories are excluded.

Only the three `OSS:MERGED`, `OSS:PENDING`, and `OSS:COUNTS` marker regions in
`README.md` are generated. The backend story, projects, contact information and
Instructor's separate upstream-incorporation credit remain hand-written. Keep the
markers intact. Friendly names and short descriptions can be edited in
`contributions.json`; new PRs use GitHub's repository name and PR title by default.

The updater uses the built-in, repository-scoped `GITHUB_TOKEN`. No personal token
or additional secret is needed. Automatic updates are committed by GitHub Actions.
Only changed lists create a commit; an hourly check does not create an activity
commit. API failures, incomplete search results, missing markers and concurrent
README edits fail the run instead of replacing the profile with partial data.

GitHub search returns at most 1,000 PRs per query. The updater fails visibly if that
limit is exceeded instead of silently dropping contributions. GitHub may disable
scheduled workflows after 60 days without repository activity; if that happens,
re-enable this workflow in the Actions tab. No empty keepalive commits are created.

To test locally:

```sh
python3 -m unittest discover -s scripts -p 'test_*.py' -v
python3 scripts/update_contributions.py --check
```

`--write` refreshes the local README. An optional `GH_TOKEN` environment variable
raises API rate limits for local checks. `--publish` is intended for this profile's
Actions context and updates the current remote README using its content SHA.
