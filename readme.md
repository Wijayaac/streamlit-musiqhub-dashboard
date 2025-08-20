# MusiqHub Dashboard — Google Drive setup

This document explains how to create Google credentials and configure your Streamlit app to read Excel files from Google Drive using a service account. It also notes the alternative OAuth (user) flow used by quickstart.py.

---

## Overview

The app authenticates to Google Drive using a Google Cloud service account. Steps:

1. Enable the Drive API in a Google Cloud project.
2. Create a service account and download its JSON key.
3. Share the target Google Drive folder with the service account email.
4. Add the JSON values to `.streamlit/secrets.toml` under the `gcp_service_account` key.
5. Restart Streamlit and verify the app can list files.

---

## 1) Enable the Drive API

- Open the Google Cloud Console: https://console.cloud.google.com
- Select (or create) a project.
- Go to "APIs & Services" → "Library" and enable the "Google Drive API" for the project.

Refer to the Drive API quickstart for Python: https://developers.google.com/drive/api/quickstart/python

---

## 2) Create a service account and key

1. In the Cloud Console, open "IAM & Admin" → "Service accounts".
2. Click `Create Service Account`.
   - Give it a name (e.g. `musiqhub-streamlit-sa`).
3. (Optional) Grant roles if your workflow needs them — for listing files and downloading files, the service account itself does not need a project-level role; access to Drive objects is controlled by sharing the folder with the service account email.
4. After creating the account, click it, then `Keys` → `Add Key` → `Create new key` → `JSON`. Download the JSON file.

Keep this JSON private. Do NOT commit it to git.

Helpful doc: https://cloud.google.com/iam/docs/creating-managing-service-account-keys

---

## 3) Share your Drive folder with the service account

- In Google Drive, locate the folder that contains your Excel source files.
- Right-click the folder → `Share` → add the service account email (found in the JSON under `client_email`) as `Viewer` or `Editor`.
- This is required because service accounts are separate accounts and do not automatically see your personal Drive files.

If your files live in a Shared Drive, make sure the service account has access to that Shared Drive or the files are moved/shared appropriately.

---

## 4) Add credentials to `.streamlit/secrets.toml`

Streamlit reads secrets from `.streamlit/secrets.toml`. Add the service account JSON content under a TOML table called `gcp_service_account`.

Example (replace values with the content of your JSON key):

```toml
[gcp_service_account]
type = "service_account"
project_id = "YOUR_PROJECT_ID"
private_key_id = "..."
private_key = """-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"""
client_email = "your-service-account@your-project.iam.gserviceaccount.com"
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."
```

Notes:

- Use triple quotes `"""` for `private_key` and preserve newlines (use `\n` if pasting on a single line).
- Do not commit `.streamlit/secrets.toml` containing real credentials to source control.
- Add `.streamlit/secrets.toml` to your `.gitignore`.

---

## 5) Local testing and troubleshooting

- Restart the Streamlit server after updating secrets.
- In your app you can verify the secret loads:

```py
import streamlit as st
st.write(st.secrets.get("gcp_service_account", {}).get("client_email"))
```

- If your app returns "No Excel files found in Google Drive folder":
  - Confirm the folder name is correct in your code or use the folder ID instead.
  - Confirm the folder is shared with the service account email.
  - For debugging, print the folder ID or list folders returned by the API and inspect errors.

Example debug snippet (inside the app):

```py
service = get_drive_service()
res = service.files().list(q="mimeType='application/vnd.google-apps.folder' and name='YOUR_FOLDER_NAME'", fields="files(id,name)").execute()
st.write(res.get('files', []))
```

---

## Alternative: OAuth 2.0 user flow (quickstart.py)

`quickstart.py` typically uses OAuth client credentials (`credentials.json`) and stores a `token.json` after the first user consent. That authenticates as your user account and can access your Drive files without needing to explicitly share folders with a service account.

Docs and quickstart: https://developers.google.com/drive/api/quickstart/python

Notes:

- OAuth is suitable for local testing but less convenient for deployed web apps.
- If using OAuth in Streamlit you must carefully handle the OAuth redirect/consent flow.

---

## Example: minimal Streamlit code to list Excel files in a folder

Your app already contains a `get_drive_service()` and `list_drive_excel_files()` function. A minimal listing example:

```py
files = list_drive_excel_files(folder_name="my-folder-name")
if not files:
    st.warning("Folder not found or no Excel files. Make sure folder is shared with the service account.")
else:
    for f in files:
        st.write(f"{f['name']} — {f['id']}")
```

---

## Security

- Never commit service account JSON or secrets.toml with live credentials to a public repository.
- Use least privilege where possible.

---

If you want, I can:

- Add a script to extract the JSON and write a properly escaped `.streamlit/secrets.toml` locally, or
- Add a small debug panel in the app to show the service account email and folder search results.
