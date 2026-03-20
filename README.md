# Git Time Agent 🤖

An AI agent that automatically reads your daily Azure DevOps git commits, 
generates a work summary using Azure OpenAI, and logs your time to the 
Trio timekeeping website.

---

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Azure OpenAI Setup](#1-azure-openai-setup)
3. [Azure DevOps PAT Setup](#2-azure-devops-pat-setup)
4. [Project Setup](#3-project-setup)
5. [Configure Environment Variables](#4-configure-environment-variables)
6. [Install Dependencies](#5-install-dependencies)
7. [Install Playwright Browser](#6-install-playwright-browser)
8. [Run the Agent](#7-run-the-agent)
9. [File Output](#8-file-output)
10. [Troubleshooting](#9-troubleshooting)

---

## Prerequisites

Before you begin, make sure you have the following installed on your machine:

- **Python 3.10 or higher**  
  Download from https://www.python.org/downloads/  
  ✅ During install, check **"Add Python to PATH"**

- **Git** (optional but recommended)  
  Download from https://git-scm.com/downloads

- **Visual Studio Code** (recommended)  
  Download from https://code.visualstudio.com/

- Access to **Azure DevOps** with at least one git repository
- Access to **Azure OpenAI** through your Azure subscription
- A **Trio** timekeeping account at https://trio.msfw.com

---

## 1. Azure OpenAI Setup

### Step 1 — Open Azure Portal
Go to https://portal.azure.com and sign in with your work account.

### Step 2 — Find Your Azure OpenAI Resource
1. In the search bar at the top, type **"Azure OpenAI"**
2. Click **Azure OpenAI** under Services
3. Click on your OpenAI resource (e.g. `open-api-resource`)

### Step 3 — Copy Your API Key
1. In the left menu click **"Keys and Endpoint"**
2. Copy **Key 1** — this is your `OPENAI_API_KEY`
3. Copy the **Endpoint** URL — this is your `OPENAI_BASE_URL`
   - It will look like: `https://your-resource-name.openai.azure.com/`

### Step 4 — Find Your Deployment Name
1. Go to https://ai.azure.com (Azure AI Studio)
2. Select your Azure OpenAI resource
3. Click **"Deployments"** in the left menu
4. Find your deployment and copy the **Deployment name** exactly
   - This is your `OPENAI_DEPLOYMENT` (e.g. `gpt-4.1`)
5. Note the **API version** from the target URI shown on the deployment page
   - This is your `OPENAI_API_VERSION` (e.g. `2025-01-01-preview`)

---

## 2. Azure DevOps PAT Setup

A Personal Access Token (PAT) allows the agent to read your commits.  
It is **read-only** and cannot modify or delete anything in your repo.

### Step 1 — Open Azure DevOps
Go to https://dev.azure.com/YOUR-ORG-NAME and sign in.

### Step 2 — Create a Personal Access Token
1. Click your **profile picture** in the top-right corner
2. Click **"Personal access tokens"**
3. Click **"+ New Token"**
4. Fill in the form:
   - **Name:** `git-time-agent` (or any name you like)
   - **Organization:** Select your organization
   - **Expiration:** Set to 90 days or custom
   - **Scopes:** Select **"Custom defined"**
     - Under **Code** → check **Read** only ✅
     - Leave everything else unchecked
5. Click **"Create"**
6. **Copy the token immediately** — you won't be able to see it again
   - This is your `AZURE_DEVOPS_PAT`

### Step 3 — Find Your Azure DevOps Details
From your Azure DevOps URL:
