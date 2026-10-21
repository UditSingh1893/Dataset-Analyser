"""Check every commit page on the default branch for co-author chips.

GitHub's REST contributors API excludes co-authors, but the commit page
renders an author chip per Co-Authored-By trailer. This walks the branch
history and reports which logins GitHub credits.
"""
import json, re, urllib.request

REPO = "UditSingh1893/Dataset-Analyser"
UA = {"User-Agent": "Mozilla/5.0"}


def get(url, max_retries=4):
    last = None
    for _ in range(max_retries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=90) as r:
                data = b""
                while True:
                    chunk = r.read(65536)
                    if not chunk:
                        break
                    data += chunk
            return data.decode("utf-8", "replace")
        except Exception as e:
            last = e
            continue
    raise last


def main():
    api = f"https://api.github.com/repos/{REPO}/commits?sha=main&per_page=100"
    shas = [c["sha"] for c in json.loads(get(api))]
    print(f"{len(shas)} commits on main\n")

    bad = 0
    for sha in shas:
        html = get(f"https://github.com/{REPO}/commit/{sha}")
        names = sorted(
            set(re.findall(r'/users/([A-Za-z0-9_-]+)/hovercard', html))
            | set(re.findall(r'"login":"([A-Za-z0-9_-]+)"', html))
        )
        trailer = "Co-Authored-By" in html
        flag = ""
        if "claude" in [n.lower() for n in names] or trailer:
            flag = "   <<<< CLAUDE CREDIT"
            bad += 1
        print(f"{sha[:8]}  credited={names}{flag}")

    print(f"\ncommits with claude credit: {bad}/{len(shas)}")


if __name__ == "__main__":
    main()
