# Jenkins Next Steps Runbook

This runbook takes you from "pipeline runs" to a repeatable CI/CD workflow with deployment and health verification.

## What Was Added

- Pipeline parameters for Python path and deployment toggles
- Local staging deployment script: `scripts/deploy_local_staging.ps1`
- Local staging stop/cleanup script: `scripts/stop_local_staging.ps1`
- Health smoke test script: `scripts/smoke_test.py`

## Jenkins Parameters (in `Jenkinsfile`)

- `WINDOWS_PYTHON`
  - Default: `C:\\Users\\Asus\\AppData\\Local\\Programs\\Python\\Python312\\python.exe`
  - Use this when Jenkins cannot discover Python from PATH.
- `DEPLOY_LOCAL_STAGING`
  - `false` by default.
  - Set to `true` when you want deployment and smoke test stages to run.
- `STAGING_ROOT`
  - Default: `C:\\JenkinsDeploy\\crm-staging`
  - Folder where backend and frontend build outputs are deployed.
- `STAGING_PORT`
  - Default: `8010`
  - Local API port used for staged backend and smoke checks.

## One-Time Jenkins Job Setup

1. Open your Pipeline job in Jenkins.
2. Confirm Pipeline script source is SCM and points to repository root `Jenkinsfile`.
3. Enable `Build with Parameters` (automatically available because parameters are defined in pipeline).
4. Set default parameter values in Jenkins UI if you want different machine paths.
5. Save job configuration.

## Run Modes

## 1) CI-only run

Use when validating code changes quickly.

- `DEPLOY_LOCAL_STAGING = false`
- Stages executed:
  - Checkout
  - Backend dependency install
  - Backend tests
  - ML model training
  - Frontend build

## 2) CI + Local CD run

Use when validating deployment workflow and runtime health.

- `DEPLOY_LOCAL_STAGING = true`
- Stages executed in addition to CI:
  - Deploy to local staging
  - Smoke test on `/health`
  - Post-build cleanup (stop staged backend)

## Configure Automatic Triggers (Webhook)

## GitHub

1. In Jenkins job, enable trigger:
   - `GitHub hook trigger for GITScm polling`
2. In GitHub repository:
   - Settings -> Webhooks -> Add webhook
   - Payload URL: `http://<jenkins-host>/github-webhook/`
   - Content type: `application/json`
   - Events: `Just the push event` (add pull_request if needed)
3. Save and test webhook delivery.

## Bitbucket

1. In Jenkins job, enable trigger:
   - Build when a change is pushed to BitBucket
2. In Bitbucket repository:
   - Repository settings -> Webhooks -> Add webhook
   - URL: `http://<jenkins-host>/bitbucket-hook/`
   - Trigger: push events
3. Save and push a small commit to validate trigger.

## Deployment Flow Details

When local deploy is enabled, `scripts/deploy_local_staging.ps1` does the following:

1. Resolves Python executable (parameter, launcher, PATH, common install paths).
2. Copies backend source + ML assets + dataset into `STAGING_ROOT`.
3. Copies frontend `dist` into `STAGING_ROOT\\frontend-dist`.
4. Creates backend virtual environment in staged folder.
5. Installs backend dependencies in staged environment.
6. Starts staged FastAPI service with uvicorn on `STAGING_PORT`.
7. Writes PID to `STAGING_ROOT\\backend.pid`.
8. Writes deployment summary to `STAGING_ROOT\\deployment-summary.txt`.

Then `scripts/smoke_test.py` polls:

- `http://127.0.0.1:<STAGING_PORT>/health`
- Pass condition: HTTP 200 and JSON response includes `{"status": "ok"}`

Finally, `scripts/stop_local_staging.ps1` is called in `post` to clean up the staged process.

## Troubleshooting

## Python not found

1. Set `WINDOWS_PYTHON` explicitly.
2. Ensure Jenkins service account can read/execute that path.
3. If Python was installed after Jenkins started, restart Jenkins service.

## Port already in use

1. Change `STAGING_PORT` parameter to another free port.
2. Re-run build.

## Smoke test failing

1. Check staged logs:
   - `C:\\JenkinsDeploy\\crm-staging\\backend.stdout.log`
   - `C:\\JenkinsDeploy\\crm-staging\\backend.stderr.log`
2. Confirm `/health` endpoint manually.

## Recommended Next Upgrades

1. Add branch-based environments (`develop` -> staging, `main` -> production).
2. Replace local deploy stage with remote deploy target (VM/App Service/Container).
3. Add secrets from Jenkins Credentials (API keys, DB URLs) instead of plain env values.
4. Add rollback script that swaps back to previous artifact if smoke test fails.


