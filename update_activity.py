"""Rewrite the <!-- activity --> block in README.md with recently pushed public repos.

Runs from GitHub Actions (see .github/workflows/activity.yml).
"""
import json, os, re, urllib.request
from datetime import datetime, timezone

USER = "umaarmirzaa"
LIMIT = 4
SKIP = {USER}  # the profile repo itself

req = urllib.request.Request(
    f"https://api.github.com/users/{USER}/repos?sort=pushed&per_page=100&type=owner",
    headers={"Accept": "application/vnd.github+json"},
)
if os.environ.get("GITHUB_TOKEN"):
    req.add_header("Authorization", "Bearer " + os.environ["GITHUB_TOKEN"])

repos = json.load(urllib.request.urlopen(req))

rows = []
for r in repos:
    if r["private"] or r["fork"] or r["name"] in SKIP:
        continue
    when = datetime.strptime(r["pushed_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    days = (datetime.now(timezone.utc) - when).days
    ago = "today" if days == 0 else "yesterday" if days == 1 else f"{days}d ago" if days < 30 else when.strftime("%b %Y")
    desc = (r["description"] or "").split(".")[0].strip()
    lang = f" · `{r['language']}`" if r["language"] else ""
    rows.append(f"- [**{r['name']}**](https://github.com/{r['full_name']}){lang} — {desc} <sub>{ago}</sub>")
    if len(rows) == LIMIT:
        break

block = "\n".join(rows) if rows else "_Nothing public lately._"

readme = open("README.md", encoding="utf-8").read()
new, n = re.subn(
    r"(<!-- activity starts -->).*?(<!-- activity ends -->)",
    lambda m: f"{m.group(1)}\n{block}\n{m.group(2)}",
    readme,
    flags=re.S,
)
assert n == 1, "activity markers not found in README.md"
open("README.md", "w", encoding="utf-8", newline="\n").write(new)
print(block)
