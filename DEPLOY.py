r"""
Sports Hub one-command deploy.
Pushes the streamlit_app + modules to Keyvaniath/bpleone-sports-hub.

Usage:  python DEPLOY.py
Token:  reads $env:GITHUB_TOKEN, falls back to ~/.pokemon_deploy_token.
"""
import base64
import json
import os
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    print("Install requests: pip install requests")
    sys.exit(1)

TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()
if not TOKEN:
    for p in (Path.home() / ".pokemon_deploy_token", Path.home() / ".bpleone_deploy_token"):
        if p.exists():
            TOKEN = p.read_text(encoding="utf-8").strip()
            break
if not TOKEN:
    print("ERR: no GITHUB_TOKEN env var and no ~/.pokemon_deploy_token file.")
    sys.exit(1)

OWNER = "Keyvaniath"
REPO = "bpleone-sports-hub"

FILES = [
    ("streamlit_app.py",   "feat: Sports Hub dashboard"),
    ("data_sources.py",    "feat: ESPN data layer"),
    ("fantasy_sleeper.py", "feat: Sleeper fantasy integration"),
    ("weather.py",         "feat: Open-Meteo weather for outdoor games"),
    ("teams_config.py",    "feat: teams config"),
    ("requirements.txt",   "deps"),
    ("README.md",          "docs"),
]

HEADERS = {
    "Authorization": "Bearer " + TOKEN,
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


def get_sha(path):
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{path}"
    r = requests.get(url, headers=HEADERS)
    if r.status_code == 200:
        return r.json().get("sha")
    return None


def repo_exists():
    r = requests.get(f"https://api.github.com/repos/{OWNER}/{REPO}", headers=HEADERS)
    return r.status_code == 200


def create_repo():
    r = requests.post(
        "https://api.github.com/user/repos",
        headers={**HEADERS, "Content-Type": "application/json"},
        data=json.dumps({
            "name": REPO,
            "description": "Personal sports dashboard for Brandon — Lakers/Dodgers/Rams/USC.",
            "private": False,
            "auto_init": True,
            "has_issues": False,
            "has_wiki": False,
        }),
    )
    if r.status_code not in (200, 201):
        print(f"  ERR creating repo: HTTP {r.status_code} - {r.text[:200]}")
        return False
    print(f"  OK  created repo {OWNER}/{REPO}")
    return True


def push(filename, message):
    p = Path(filename)
    if not p.exists():
        print("  X MISSING: " + filename)
        return
    content_b64 = base64.b64encode(p.read_bytes()).decode()
    sha = get_sha(filename)
    payload = {"message": message, "content": content_b64, "branch": "main"}
    if sha:
        payload["sha"] = sha
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{filename}"
    r = requests.put(
        url,
        headers={**HEADERS, "Content-Type": "application/json"},
        data=json.dumps(payload),
    )
    if r.status_code in (200, 201):
        commit_sha = r.json().get("commit", {}).get("sha", "?")[:7]
        size_kb = len(p.read_bytes()) / 1024
        print(f"  OK  {filename:30s} ({size_kb:6.1f} KB) -> {commit_sha}")
    else:
        print(f"  ERR {filename}: HTTP {r.status_code} - {r.text[:200]}")


if __name__ == "__main__":
    os.chdir(Path(__file__).parent)
    print(f"Deploying from: {Path.cwd()}")
    print(f"Target: {OWNER}/{REPO}")
    print()

    if not repo_exists():
        print(f"  Repo not found, creating {OWNER}/{REPO}...")
        if not create_repo():
            sys.exit(1)

    for entry in FILES:
        push(*entry)

    print()
    print("Done.")
    print("Next steps if not already configured:")
    print("  1. Streamlit Community Cloud: connect repo, app file = streamlit_app.py")
    print("  2. Custom domain: sports.bpleone.com -> Streamlit CNAME")
    print("  3. Wait ~60s for build, hard-refresh sports.bpleone.com")
