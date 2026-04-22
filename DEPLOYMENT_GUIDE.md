# 🚀 Digital Scriptorium - Streamlit Cloud Deployment Guide

Deploying your Digital Scriptorium application to Streamlit Community Cloud (via GitHub) is a straightforward process. Follow these exact steps to ensure a secure, robust deployment.

---

## ✅ Phase 1: Local Preparation (Already Completed)

We have already stabilized the application environment:
1. **Dependency Pinning:** All system requirements are securely locked in `requirements.txt`.
2. **Security Locking:** A `.gitignore` file has been created to prevent your `.streamlit/secrets.toml` from being uploaded to public or private version control. Your API keys are strictly protected.

---

## 🐙 Phase 2: Uploading to GitHub

To deploy from Streamlit Cloud, the source code must securely exist inside a GitHub repository.

### Step 1: Initialize Git
Open your command prompt or terminal in your `e:\IIIF` folder and run:
```bash
git init
git add .
git commit -m "🚀 Initial release of Digital Scriptorium"
```

### Step 2: Create a GitHub Repository
1. Log in to [GitHub](https://github.com).
2. Click the **+** (plus) icon in the top right corner and select **New repository**.
3. Name your repository (e.g., `digital-scriptorium`), leave it **Public** or **Private** (both work with Streamlit Community Cloud), and click **Create repository**. 
*(Make sure NOT to add a README, .gitignore, or license file right now).*

### Step 3: Push Your Code
Follow the instructions provided by GitHub to push your local directory. It typically looks like this:
```bash
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/digital-scriptorium.git
git push -u origin main
```

---

## ☁️ Phase 3: Deploying to Streamlit Community Cloud

Now that GitHub has your code, we will connect Streamlit to run it automatically.

### Step 1: Connect to Streamlit
1. Go to [share.streamlit.io](https://share.streamlit.io) and log in with your GitHub account.
2. Click on the **New app** button.
3. If prompted, authorize Streamlit to access your GitHub repositories.

### Step 2: Configure the App
Fill in the deployment form:
- **Repository**: Select your newly created repository (e.g., `YOUR_USERNAME/digital-scriptorium`).
- **Branch**: Select `main`.
- **Main file path**: Type `streamlit_app.py`.

### 🚨 Step 3: Injecting the Secure Secrets (CRITICAL)
Because we deliberately ignored `.streamlit/secrets.toml` from GitHub to protect your API keys, the Cloud server currently does not know how to connect to Supabase or OpenAI.

1. At the bottom of the Streamlit deployment screen, click **Advanced settings**.
2. Under the **Secrets** section, paste the exact contents of your local `e:\IIIF\.streamlit\secrets.toml` file.

It should look something like this:
```toml
[openai]
api_key = "sk-..."

[supabase]
url = "https://wfufewwhryixbhrmcpah.supabase.co"
key = "eyJh..."
```
3. Click **Save** to lock in the secrets.

### Step 4: Launch!
Click the **Deploy!** button. 

Grab a cup of coffee. The Streamlit servers will spin up a fresh Linux container, download your `requirements.txt`, install your dependencies, and launch your application. 

---

## 🎉 Post-Deployment Management

* **URL Integration**: You will be assigned a permanent Streamlit app URL (e.g., `https://digital-scriptorium.streamlit.app/`). Feel free to share this!
* **Continuous Updates**: Moving forward, whenever you run `git push` to upload new code changes to GitHub, Streamlit Cloud will instantly detect the update and automatically redeploy your app within 30 seconds. No further configuration is needed!

**You are fully live!** 🏛️✨
