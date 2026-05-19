# Moodle → Google Drive Auto-Sync

Automatically downloads all course materials from Moodle and uploads them to Google Drive, organized by section and module — mirroring the exact structure in Moodle.

---

## Requirements

- Python 3.10+
- Google account with Google Drive API enabled
- Moodle account with username/password login (not external SSO)

---

## Setup (One-time)

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Create credentials.json from Google Cloud Console

1. Go to [https://console.cloud.google.com](https://console.cloud.google.com)
2. Create a new project (e.g. `moodle-sync`)
3. Sidebar → **APIs & Services** → **Library**
4. Search **Google Drive API** → click **Enable**
5. Go to **APIs & Services** → **OAuth consent screen**
   - User Type: **External** → click Create
   - Fill in App name, User support email, Developer contact email → Save
   - Under **Test users** → click **Add users** → enter your Google email → Save
6. Go to **APIs & Services** → **Credentials**
   - Click **+ Create Credentials** → **OAuth client ID**
   - Application type: **Desktop app** → give it a name → click **Create**
   - Click **Download JSON** on the newly created credential
7. Rename the downloaded file to `credentials.json`
8. Place `credentials.json` in the same folder as `moodle_sync.py`

> **Why add Test users?**  
> Unverified OAuth apps can only be used by emails registered as test users. Skipping this step will result in a 403 error during authorization.

### 3. Configure the script

Open `moodle_sync.py` and edit this section:

```python
MOODLE_URL          = "https://elearning.yourschool.edu"  # Your Moodle URL
USERNAME            = "your_username"
PASSWORD            = "your_password"
GDRIVE_FOLDER_NAME  = "Course Materials"                  # Root folder name in Drive
```

---

## Usage

```bash
python3 moodle_sync.py
```

- **First run**: a browser window opens for Google Drive authorization → allow access → token saved to `token.pickle`
- **Subsequent runs**: fully automatic, no browser needed
- **Incremental sync**: files already in Drive are skipped — only new files get uploaded

---

## Google Drive Folder Structure

Folders are created automatically to mirror Moodle:

```
Course Materials/
├── Course Name/
│   ├── Section Name/
│   │   ├── Module Name/
│   │   │   ├── file.pdf
│   │   │   └── slides.pptx
│   │   └── Another Module/
│   │       └── assignment.docx
│   └── Another Section/
│       └── ...
└── Another Course/
    └── ...
```

---

## Configuration Options

| Variable | Default | Description |
|---|---|---|
| `SKIP_EXISTING` | `True` | Skip files already in Drive (incremental sync) |
| `DOWNLOAD_DIR` | `./downloads` | Local temp folder before upload |

---

## Automate with Cron (Optional)

Example: run every day at 7:00 AM:

```bash
crontab -e
# Add this line:
0 7 * * * cd /path/to/folder && PYTHONUNBUFFERED=1 python3 moodle_sync.py >> sync.log 2>&1
```

---

## Troubleshooting

| Error | Solution |
|---|---|
| `Login failed` | Check USERNAME/PASSWORD. Make sure login works via the standard form, not external SSO/LDAP |
| `credentials.json not found` | Make sure the file is in the same folder as the script |
| 403 error during OAuth | Add your Google email as a Test user in the OAuth consent screen (see step 5 above) |
| File not downloaded | Resources of type `url` (external links) or `forum` are skipped — only downloadable files are synced |
| `token.pickle` expired | Delete `token.pickle`, re-run the script, and re-authorize in the browser |
