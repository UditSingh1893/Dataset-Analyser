"""Render a GitHub URL headlessly and report contributor-widget findings."""
import os, re, shutil, subprocess, sys, tempfile

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

def render(url, budget=20000):
    prof = tempfile.mkdtemp(prefix="cg_")
    out = subprocess.run(
        [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
         f"--user-data-dir={prof}", f"--virtual-time-budget={budget}", "--dump-dom", url],
        capture_output=True, text=True, timeout=180,
    ).stdout
    shutil.rmtree(prof, ignore_errors=True)
    return out

def report(url, html):
    print(f"=== {url}")
    print(f"  size={len(html)}")
    ids = set(re.findall(r"avatars\.githubusercontent\.com/u/(\d+)", html))
    logins = set(re.findall(r'/users/([A-Za-z0-9_-]+)/hovercard', html))
    print(f"  avatar user ids: {sorted(ids)}")
    print(f"  hovercard logins: {sorted(logins)}")
    # contributor list section
    i = html.find("Contributors</span>")
    if i != -1:
        seg = html[i:i+4000]
        m = re.search(r'CounterLabel[^>]*>(?:<span>)?([0-9]+)', seg)
        print(f"  count badge: {m.group(1) if m else '?'}")
        names = re.findall(r'contributorName__\w+[^>]*title="([^"]*)"', seg)
        print(f"  listed contributors: {names}")
    print(f"  claude mentions: {len(re.findall(r'[Cc]laude', html))}")
    print()

if __name__ == "__main__":
    for url in sys.argv[1:]:
        report(url, render(url))
