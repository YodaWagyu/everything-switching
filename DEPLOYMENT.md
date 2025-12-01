# Deployment Guide

## Quick Deployment Steps

### 1. Initialize Git (if not already done)

```bash
cd /path/to/everything-switching
git init
git add .
git commit -m "Initial commit: Everything-Switching Analysis Dashboard"
```

### 2. Create GitHub Repository

1. Go to [github.com/new](https://github.com/new)
2. Repository name: `everything-switching`
3. Description: `Customer Switching Analysis Dashboard with BigQuery & AI`
4. Choose: **Private** or **Public**
5. **DO NOT** initialize with README (we already have one)
6. Click "Create repository"

### 3. Push to GitHub

Replace `YOUR_USERNAME` with your GitHub username:

```bash
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/everything-switching.git
git push -u origin main
```

### 4. Deploy to Streamlit Cloud

#### 4.1 Go to Streamlit Cloud
- Visit: [share.streamlit.io](https://share.streamlit.io)
- Sign in with GitHub

#### 4.2 Create New App
- Click "New app" button
- Repository: Select `YOUR_USERNAME/everything-switching`
- Branch: `main`
- Main file path: `app.py`
- Click "Deploy"

#### 4.3 Configure Secrets
While app is deploying:

1. Click "Settings" ⚙️ in your app
2. Go to "Secrets" tab
3. Copy-paste this template and **fill in your actual values**:

```toml
[bigquery]
project_id = "your-gcp-project-id"
dataset_id = "your-dataset-id"
type = "service_account"
private_key_id = "your-private-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\nYour-Private-Key-Here\n-----END PRIVATE KEY-----\n"
client_email = "your-service-account@your-project.iam.gserviceaccount.com"
client_id = "your-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project.iam.gserviceaccount.com"

[openai]
api_key = "sk-your-openai-api-key-here"

[cost]
cost_per_gb = 0.17
```

4. Click "Save"
5. App will automatically restart with secrets!

### 5. Get Your Credentials

#### BigQuery Service Account
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Select your project
3. Go to "IAM & Admin" → "Service Accounts"
4. Create or select service account
5. Click "Keys" → "Add Key" → "Create new key"
6. Choose "JSON"
7. Download the JSON file
8. Copy values from JSON to secrets.toml

#### OpenAI API Key
1. Go to [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Click "Create new secret key"
3. Copy the key (starts with `sk-`)
4. Paste in `secrets.toml`

### 6. Test Your App

1. Wait for deployment to complete (~2-3 minutes)
2. Click "Open app" button
3. Try "Use Mock Data" first to verify app works
4. Uncheck "Use Mock Data" to test BigQuery connection
5. Test AI insights generation

### 7. Updating Your App

Whenever you make changes:

```bash
git add .
git commit -m "Description of changes"
git push
```

Streamlit Cloud will automatically redeploy!

## Troubleshooting

### App won't start
- Check "Manage app" → "Logs" for errors
- Verify all secrets are correctly formatted
- Make sure requirements.txt includes all dependencies

### BigQuery connection fails
- Verify service account has BigQuery permissions
- Check project_id and dataset_id are correct
- Ensure private_key has proper line breaks (`\n`)

### OpenAI errors
- Verify API key is valid and active
- Check you have credits in your OpenAI account
- Ensure key starts with `sk-`

### Secrets not loading
- Make sure secrets are in TOML format (no tabs, proper quotes)
- Check for typos in secret keys
- Save and restart app after changes

## Local Development

To run locally:

1. Create `.streamlit/secrets.toml` (copy from `.streamlit/secrets.toml.example`)
2. Fill in your actual credentials
3. Run: `streamlit run app.py`

**IMPORTANT**: Never commit `.streamlit/secrets.toml` to git! (It's already in `.gitignore`)

## App URLs

- **Streamlit Cloud**: `https://<your-app-name>.streamlit.app`
- **GitHub Repo**: `https://github.com/<YOUR_GITHUB_USERNAME>/everything-switching`

---

**Ready to deploy!** 🚀

Follow the steps above, and your app will be live in minutes!
