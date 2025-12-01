# GitHub Desktop Deployment Guide

## Quick Start with GitHub Desktop

### 1. Open Project in GitHub Desktop

1. Open **GitHub Desktop**
2. Click **File** → **Add local repository**
3. Browse to your project folder: `C:\path\to\everything-switching`
4. Click **Add repository**

If it says "This directory does not appear to be a Git repository":
- Click **Create a repository** instead
- Name: `everything-switching`
- Description: `Customer Switching Analysis Dashboard`
- Click **Create repository**

### 2. Review Changes

In GitHub Desktop, you should see all your files listed in the "Changes" tab:
- ✅ app.py
- ✅ config.py
- ✅ requirements.txt
- ✅ README.md
- ✅ DEPLOYMENT.md
- ✅ modules/
- ✅ .streamlit/
- etc.

### 3. Make Initial Commit

1. In the bottom left:
   - **Summary**: `Initial commit`
   - **Description**: `Everything-Switching Analysis Dashboard with BigQuery & AI`
2. Click **Commit to main**

### 4. Publish to GitHub

1. Click **Publish repository** button (top right)
2. Settings:
   - Name: `everything-switching`
   - Description: `Customer Switching Analysis Dashboard`
   - ☑️ Keep this code private (recommended if using real credentials)
   - Leave organization as: Your account
3. Click **Publish repository**

✅ Your code is now on GitHub!

### 5. Deploy to Streamlit Cloud

#### 5.1 Access Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub

#### 5.2 Create New App
1. Click **New app**
2. Settings:
   - Repository: `<YOUR_GITHUB_USERNAME>/everything-switching`
   - Branch: `main`
   - Main file path: `app.py`
3. Click **Deploy**

#### 5.3 Add Secrets (IMPORTANT!)
While deploying:

1. Click **Settings** ⚙️
2. Go to **Secrets** tab
3. Paste your secrets:

```toml
[bigquery]
project_id = "your-gcp-project-id"
dataset_id = "your-dataset-id"
type = "service_account"
private_key_id = "your-private-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\nYour-Actual-Private-Key\n-----END PRIVATE KEY-----\n"
client_email = "your-service-account@your-project.iam.gserviceaccount.com"
client_id = "your-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project.iam.gserviceaccount.com"

[openai]
api_key = "sk-your-actual-openai-key"

[cost]
cost_per_gb = 0.17
```

4. Click **Save**
5. App will restart automatically!

### 6. Future Updates

Whenever you change code:

1. Save your files
2. Open **GitHub Desktop**
3. Review changes in "Changes" tab
4. Add commit message (e.g., "Updated filters UI")
5. Click **Commit to main**
6. Click **Push origin** (top right)

✅ Streamlit Cloud will auto-deploy your changes!

## Quick Checklist

- [ ] Open project in GitHub Desktop
- [ ] Make initial commit
- [ ] Publish to GitHub
- [ ] Deploy to Streamlit Cloud
- [ ] Add secrets in Streamlit
- [ ] Test the app!

## Troubleshooting

### "This directory does not appear to be a Git repository"
→ Use **Create a repository** instead of **Add local repository**

### Can't find my repository in Streamlit Cloud
→ Make sure you published it (not just committed locally)

### App crashes on Streamlit Cloud
→ Check **Manage app** → **Logs** for error messages
→ Verify secrets are correctly formatted

### Changes not showing on live app
→ Check GitHub Desktop - did you **Push origin**?
→ May take 1-2 minutes to redeploy

## Where to Get Credentials

### BigQuery Service Account
1. [Google Cloud Console](https://console.cloud.google.com)
2. IAM & Admin → Service Accounts
3. Create/Select account → Keys → Add Key → JSON
4. Download and copy values to secrets

### OpenAI API Key
1. [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Create new secret key
3. Copy (starts with `sk-`)

---

**You're all set!** 🚀

Your app will be live at: `https://<your-app-name>.streamlit.app`
