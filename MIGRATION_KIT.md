# Migration Kit — Dataset Analyser → fresh repo (clean Contributor widget)

**Why:** GitHub's Contributor widget on the current repo still lists `claude` even though every commit on `main` is trailer-free. The widget reads a contributor index that includes orphaned commit objects GitHub still retains; the graph API and REST API don't. A **fresh repo** has no orphans, so the widget is guaranteed clean from the first minute.

**What is NOT affected:** your render.com services. Verified chain — Render never reads from GitHub:

```
git push → GitHub Actions cd.yml → verify → build & push images to Docker Hub
        → curl Render Deploy Hooks → Render pulls image from Docker Hub → redeploy
```

Render source: **Docker Hub only** (`uditsingh1893/dataset-analyser-frontend` / `-backend`). Auto-Deploy is off; Render is only ever triggered by the deploy-hook curl.

---

## Part A — You do these (browser, ~10 min)

### Step 1 · Create the new repo

GitHub → **New repository** →
- Owner: `UditSingh1893`
- Name: `Dataset-Analyser-v2` *(any name works; must be NEW, not a rename)*
- Visibility: **Public** (matches current repo)
- ❌ Do NOT tick "Add a README" / "Add .gitignore" / "Choose a license" — the history must come from your local repo
- Click **Create repository**

### Step 2 · Copy the 5 secrets to the new repo

New repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret** (×5)

| # | Secret name | Value |
|---|---|---|
| 1 | `DOCKER_HUB_USERNAME` | `uditsingh1893` |
| 2 | `DOCKER_HUB_TOKEN` | your Docker Hub access token (publish + read:write) |
| 3 | `NEXT_PUBLIC_BACKEND_URL` | `https://dataset-analyser.onrender.com` |
| 4 | `RENDER_DEPLOY_HOOK_BACKEND` | Render → *Backend service* → Settings → **Deploy Hook** → copy URL |
| 5 | `RENDER_DEPLOY_HOOK_FRONTEND` | Render → *Frontend service* → Settings → **Deploy Hook** → copy URL |

> To read secret #2: Docker Hub → your avatar → **Account Settings** → **Personal Access Tokens** → *Generate new token* → scopes `read`, `write`, `delete` → copy the token string. Docker Hub only shows it once.

### Step 3 · Confirm Render auto-deploy is OFF

Render dashboard → both services → **Settings** → **Auto-Deploy** = **No**.

(If it were on, Render would redeploy on every GitHub push and bypass the CI gate — your `CI_CD_GUIDE.md` already documents turning it off.)

---

## Part B — Run these (terminal, in order)

Open a terminal in the repo folder.

```bash
cd "/c/Users/Udit Singh/OneDrive/Desktop/CV fixer/Dataset-Analyser"
```

### Step 4 · Point the remote at the new repo

```bash
git remote set-url origin https://github.com/UditSingh1893/Dataset-Analyser-v2.git
git remote -v
```

> If you'd rather not repoint the old one: `git remote rename origin old-origin` then `git remote add origin <new-url>`. Either is fine.

### Step 5 · Push the clean history

```bash
git push -f origin main
```

> `-f` is required only if the new repo has a conflicting history. If it errors "rejected", it's because the new repo auto-created a commit — delete that repo and re-create it without a README.

Expected output: `* [new branch] main -> main` or `main -> main (forced update)`

### Step 6 · Wait 2 minutes, then check the widget

Open `https://github.com/UditSingh1893/Dataset-Analyser-v2` and look at the **Contributors** widget. It must show **1** contributor: `Udit Singh`. It should not mention `claude`.

### Step 7 · Trigger CI/CD

```bash
git push origin main
```

Watch **Actions** tab. Expect two green runs:
- `CI — Lint & Build`
- `CD — Build & Push Docker Images`

The CD run does: verify → build+push both images to Docker Hub → ping both Render deploy hooks.

### Step 8 · Verify the deployment

```bash
# 1. Docker Hub got new tags
curl -sL "https://hub.docker.com/v2/repositories/uditsingh1893/dataset-analyser-frontend/tags/?page_size=5" | python -c "import json,sys; [print('  ',t['name'],t['last_updated']) for t in json.load(sys.stdin)['results']]"

# 2. Frontend still live and still pointing at the backend
curl -sL -o /dev/null -w "frontend: %{http_code}\n" https://dataset-bias-analyser.onrender.com
curl -sL -o /dev/null -w "backend:  %{http_code}\n" https://dataset-analyser.onrender.com/openapi.json

# 3. Contributor widget (should be 1)
curl -sL -H "Accept: application/json" https://github.com/UditSingh1893/Dataset-Analyser-v2/_sidebar | python -c "import json,sys; c=json.load(sys.stdin)['contributors']; print('  count:',c['contributorCount'],[x['login'] for x in c['contributors']])"
```

Expected: `count: 1 ['UditSingh1893']`, `frontend: 200`, `backend: 200`

---

## Part C — Update references and retire the old repo

### Step 9 · Update the clone URL in README

Edit the clone URL in `README.md`:

```
git clone https://github.com/UditSingh1893/Dataset-Analyser-v2.git
```

Also check `MIGRATION_KIT.md` itself and any other `Dataset-Analyser.git` mentions:

```bash
grep -rn "Dataset-Analyser.git" --include="*.md" .
```

Commit and push:

```bash
git add -A && git commit -m "docs: point clone URL at the new repository" && git push origin main
```

### Step 10 · Archive (don't delete) the old repo

Old repo → **Settings** → **Archive this repository**.

Archiving keeps the old URL alive (it 301-redirects) and keeps the repo readable, so anyone who cloned it before is unaffected. Deleting outright would break those clones and any Render config still pointing at it.

---

## Rollback

If anything goes wrong, the old repo is untouched and still has the full history:

```bash
git remote set-url origin https://github.com/UditSingh1893/Dataset-Analyser.git
```

---

## Notes

- The current `main` is **18 commits**, all authored by `Udit Singh <uditsingh1893@gmail.com>`, **zero** `Co-Authored-By` trailers. Nothing needs rewriting — the fresh repo just inherits it.
- The Docker Hub namespace is `uditsingh1893` (lowercase — Docker rejects uppercase). `UditSingh1893` is the *GitHub* name.
- The frontend service host is `dataset-bias-analyser.onrender.com`; the backend is the separate `dataset-analyser.onrender.com`. They are two different services, not a typo.
- The old repo's widget may still show `claude` for a while (until GitHub re-indexes the orphans). That's cosmetic and independent of the new repo.
