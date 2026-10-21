# Migration Kit — Dataset Analyser

Do **this** in order. A numbered checklist:

1. Work locally (branch + commit); push with `--force` in step 4 only
2. Create a **new** repo under your account: `UditSingh1893/Dataset-Analyser-v2` (or any name)
3. Replace every reference to the old clone URL in `README.md`, `CI_CD_GUIDE.md`, and `docker-compose.yml` if present
4. Force-push the new remote `main`: `git push --force origin main`
5. Wait 2 minutes, then check the Contributor widget at the new URL
6. Add the 5 GitHub Actions secrets (see step-by-step below)
7. Push another commit to trigger CI/CD: `git push origin main`
8. Verify Docker Hub tags appear and Render deploy hook fires automatically
9. Confirm live services still serve
10. Read the verification guide before deleting the old repo

A short version of everything, in order, for quick copying:

```
git branch migration
git checkout migration
git add -A && git commit -m "migration prep"
git push origin migration
# create new repo UditSingh1893/Dataset-Analyser-v2
# add _scratch/, .gitignore entries, README clone URL, secrets (see below)
git remote set-url origin https://github.com/UditSingh1893/Dataset-Analyser-v2.git
git push -f origin main
# wait 2 min, open contributor widget, verify it says 1
git push origin main         # triggers CI + CD, writes docker tags
cd /c/Users/Udit Singh/OneDrive/Desktop/CV fixer/Dataset-Analyser-v2   # wait for sync
# verify Docker Hub, Render hooks, live website
# then: archive the old repo (settings -> Darchive), don't delete
```

---

## Secret checklist

Add these 5 secrets to the new repo (Settings → Secrets → Actions):

| Secret | Value | What it is |
|---|---|---|
| `DOCKER_HUB_USERNAME` | `uditsingh1893` | The lowercase Docker Hub username the images were pushed under |
| `DOCKER_HUB_TOKEN` | *your Docker Hub access token* | PAT with publish + read:write |
| `NEXT_PUBLIC_BACKEND_URL` | `https://dataset-analyser.onrender.com` | Backend service URL that's baked into the frontend build |
| `RENDER_DEPLOY_HOOK_BACKEND` | *copy from Render Backend settings → Deploy Hook* | Webhook endpoint that triggers the backend redeploy |
| `RENDER_DEPLOY_HOOK_FRONTEND` | *copy from Render Frontend settings → Deploy Hook* | Webhook endpoint that triggers the frontend redeploy |

## Render dashboard checklist

- Backend → **Auto-Deploy**: No
- Frontend → **Auto-Deploy**: No
- Copy both Deploy Hook URLs into step 5 above

## Verification checklist

After pushing the clean history (`git push origin main`):

1. **Contributor widget** — open the new repo URL and confirm the Contributors widget shows only `Udit Singh` (1 contributor)
2. **Docker Hub** — confirm tags `latest` and `sha-<new>` show on `uditsingh1893/dataset-analyser-{frontend,backend}`
3. **Render hooks** — open the Actions page, confirm `CD — Build & Push Docker Images` runs green; the deploy-hook curl fires automatically after
4. **Live site** — confirm `https://dataset-bias-analyser.onrender.com` serves and calls `https://dataset-analyser.onrender.com/openapi.json`
5. **Old repo** — archive it in Settings (don't delete) so the redirect stays intact