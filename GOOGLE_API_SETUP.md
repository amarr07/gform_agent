# Google Forms API Setup Guide

## Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Enter project name: `political-survey-forms` 
4. Click "Create"

## Step 2: Enable Required APIs

1. In the Google Cloud Console, go to "APIs & Services" → "Library"
2. Search for and enable these APIs:
   - **Google Forms API**
   - **Google Drive API**

## Step 3: Create OAuth Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. If prompted, configure the OAuth consent screen:
   - Choose "External" user type
   - Fill in app name: "Political Survey Forms Agent"
   - Add your email as developer contact
   - Save and continue through the steps
4. For OAuth client ID:
   - Application type: "Desktop application"
   - Name: "Political Survey Agent"
   - Click "Create"
5. Download the JSON file
6. Rename it to `credentials.json` and place in project folder

## Step 4: Configure OAuth Consent Screen (Important!)

1. Go to "APIs & Services" → "OAuth consent screen"
2. Add your email to "Test users" section
3. This allows you to use the app during development

## Step 5: Verify Setup

Run the setup script:
```bash
python3 setup.py
```

## Step 6: First Run

When you run the main script for the first time:
```bash
python3 main.py
```

A browser window will open asking you to:
1. Choose your Google account
2. Grant permissions to access Google Forms and Drive
3. The app will save authentication tokens automatically

## Troubleshooting

### "App not verified" warning
- Click "Advanced" → "Go to Political Survey Agent (unsafe)"
- This is normal for development apps

### Permission errors
- Make sure your email is added to test users
- Ensure both Google Forms API and Drive API are enabled

### File not found errors
- Ensure `credentials.json` is in the project root
- Check the JSON format matches the template

## Sample credentials.json structure:
```json
{
  "installed": {
    "client_id": "your-id.apps.googleusercontent.com",
    "project_id": "your-project-id",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "your-client-secret",
    "redirect_uris": ["http://localhost"]
  }
}
```
