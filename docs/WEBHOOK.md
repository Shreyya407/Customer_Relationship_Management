
```markdown
# 🚀 Jenkins + GitHub Webhook Setup (Using ngrok)

This guide helps you connect GitHub → Jenkins (running locally) using ngrok.

---

## 📌 Prerequisites

- Jenkins running locally:
```

[http://localhost:8080](http://localhost:8080)

```
- Pipeline job created (e.g., `Proj`)
- GitHub repository ready
- ngrok installed

---

## 🔧 Step 1: Start Jenkins

Make sure Jenkins is running:

```

[http://localhost:8080](http://localhost:8080)

````

---

## 🌐 Step 2: Start ngrok

Expose Jenkins to the internet:

```bash
ngrok http 8080
````

You will see output like:

```
Forwarding https://abc123.ngrok-free.app -> http://localhost:8080
```

👉 Copy the HTTPS URL

---

## 🔗 Step 3: Webhook URL

Construct your webhook endpoint:

```
https://<your-ngrok-url>/github-webhook/
```

Example:

```
https://abc123.ngrok-free.app/github-webhook/
```

---

## ⚙️ Step 4: Configure Jenkins Job

Go to:

```
http://localhost:8080/job/Proj/configure
```

Enable:

* ✅ GitHub hook trigger for GITScm polling

Save the job.

---

## 🐙 Step 5: Create GitHub Webhook

Go to your GitHub repository:

```
Settings → Webhooks → Add webhook
```

Fill the details:

### Payload URL

```
https://<your-ngrok-url>/github-webhook/
```

### Content Type

```
application/json
```

### Events

* Select: Just the push event
* (Optional later: add Pull requests)

### Active

* ✅ Checked

Click **Add webhook**

---

## 🧪 Step 6: Test Webhook

Make a commit:

```bash
git add .
git commit -m "test webhook"
git push
```

---

## 🔍 Step 7: Verify

### GitHub

* Go to Webhooks → Recent Deliveries
* Check:

  * Status = 200 ✅

### Jenkins

```
http://localhost:8080/job/Proj/
```

* A new build should trigger automatically 🎉

---

## ⚙️ Step 8: Run Deployment (Optional)

Go to Jenkins:

👉 Build with Parameters

Set:

```
DEPLOY_LOCAL_STAGING = true
```

Run build.

---

## 🌐 Step 9: Verify Application

Open:

```
http://127.0.0.1:8010/health
```

Expected:

```json
{"status": "ok"}
```

---

## 🚨 Troubleshooting

### ❌ Webhook not triggering

* Check GitHub → Recent Deliveries
* Ensure status is 200

---

### ❌ 404 Error

* Ensure URL ends with:

```
/github-webhook/
```

---

### ❌ Timeout

* ngrok is not running
* Restart:

```bash
ngrok http 8080
```

---

### ❌ Jenkins not building

* Ensure:

  * Pipeline is "Pipeline from SCM"
  * Repo URL is correct
  * Branch matches (main/master)

---

## ⚠️ Important Notes

* ngrok URL changes on restart

  * Update webhook if needed

* Jenkins must be running before ngrok

---

## 🧠 Flow Overview

```
GitHub Push
   ↓
Webhook (ngrok URL)
   ↓
Jenkins (/github-webhook/)
   ↓
Pipeline Job (Proj)
   ↓
Build + Test + Deploy
```

---

## 🚀 Next Steps

* Add Pull Request triggers
* Add Docker support
* Deploy to AWS / Cloud
* Add rollback + monitoring

```

---
