#!/usr/bin/env python3
"""
Moodle → Google Drive Auto-Sync
Otomatis download semua materi dari Moodle dan upload ke Google Drive
"""

import os
import re
import sys
import json
import time
import pickle
import requests
import urllib3
from pathlib import Path

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ============================================================
# ⚙️  KONFIGURASI — Edit bagian ini sesuai kebutuhanmu
# ============================================================
MOODLE_URL          = "https://adg.moodle-kurse.de"
USERNAME            = "wildanfirdaus.alhafidz"
PASSWORD            = "Hahahaha0!"
DOWNLOAD_DIR        = Path("./downloads")
GDRIVE_FOLDER_NAME  = "ADG downloads"
SKIP_EXISTING       = True
# ============================================================

SCOPES = ['https://www.googleapis.com/auth/drive']
FAILED_LOG = Path("failed_files.json")

# ── Warna terminal ────────────────────────────────────────────
class C:
    GREEN  = "\033[92m"
    RED    = "\033[91m"
    YELLOW = "\033[93m"
    CYAN   = "\033[96m"
    BOLD   = "\033[1m"
    RESET  = "\033[0m"

def ok(msg):    print(f"{C.GREEN}✅  {msg}{C.RESET}")
def err(msg):   print(f"{C.RED}❌  {msg}{C.RESET}")
def info(msg):  print(f"{C.CYAN}ℹ️   {msg}{C.RESET}")
def warn(msg):  print(f"{C.YELLOW}⚠️   {msg}{C.RESET}")
def skip(msg):  print(f"    ⏭️  {msg}")
def upload(msg):print(f"    ☁️  {msg}")


# ═══════════════════════════════════════════════════════════════
# MOODLE REST API
# ═══════════════════════════════════════════════════════════════

def moodle_get_token() -> str:
    """Dapatkan token Moodle via REST API."""
    resp = requests.post(
        f"{MOODLE_URL}/login/token.php",
        data={"username": USERNAME, "password": PASSWORD, "service": "moodle_mobile_app"},
        timeout=15,
        verify=False,
    )
    data = resp.json()
    if "token" not in data:
        raise RuntimeError(f"Login gagal: {data.get('error', data)}")
    return data["token"]


def moodle_api(token: str, function: str, **params) -> any:
    """Panggil Moodle Web Service REST API."""
    resp = requests.get(
        f"{MOODLE_URL}/webservice/rest/server.php",
        params={"wstoken": token, "wsfunction": function, "moodlewsrestformat": "json", **params},
        timeout=30,
        verify=False,
    )
    data = resp.json()
    if isinstance(data, dict) and data.get("exception"):
        raise RuntimeError(f"API error [{function}]: {data.get('message')}")
    return data


def get_enrolled_courses(token: str) -> list[dict]:
    """Ambil user info lalu semua course yang di-enroll."""
    site_info = moodle_api(token, "core_webservice_get_site_info")
    userid = site_info["userid"]

    courses = moodle_api(token, "core_enrol_get_users_courses", userid=userid)
    info(f"Ditemukan {len(courses)} course")
    return [{"id": c["id"], "name": c["displayname"]} for c in courses]


def get_files_from_course(token: str, course: dict) -> list[dict]:
    """Ambil semua file dari course via course contents API."""
    sections = moodle_api(token, "core_course_get_contents", courseid=course["id"])

    files = []
    DOWNLOADABLE = {"resource", "folder", "assign"}

    for section in sections:
        for mod in section.get("modules", []):
            if mod.get("modname") not in DOWNLOADABLE:
                continue
            for content in mod.get("contents", []):
                if content.get("type") != "file":
                    continue
                fileurl = content.get("fileurl", "")
                if not fileurl:
                    continue
                # API file URLs butuh token sebagai query param
                if "?" in fileurl:
                    fileurl += f"&token={token}"
                else:
                    fileurl += f"?token={token}"
                files.append({
                    "name":     content.get("filename", "unknown"),
                    "url":      fileurl,
                    "section":  section.get("name", ""),
                    "module":   mod.get("name", ""),
                })
    return files


def download_file(url: str, dest_dir: Path, filename: str) -> Path | None:
    """Download satu file, return path atau None jika gagal."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    filepath = dest_dir / _sanitize(filename)

    resp = requests.get(url, stream=True, timeout=60, verify=False)
    if resp.status_code != 200:
        return None

    total = 0
    with open(filepath, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
            total += len(chunk)

    if total == 0:
        filepath.unlink(missing_ok=True)
        return None

    return filepath


def _sanitize(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', "_", name)


# ═══════════════════════════════════════════════════════════════
# GOOGLE DRIVE
# ═══════════════════════════════════════════════════════════════

def authenticate_drive():
    """OAuth2 authentication untuk Google Drive API."""
    creds = None
    token_path = Path("token.pickle")

    if token_path.exists():
        with open(token_path, "rb") as f:
            creds = pickle.load(f)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, "wb") as f:
            pickle.dump(creds, f)

    return build("drive", "v3", credentials=creds)


def get_or_create_folder(service, name: str, parent_id: str | None = None) -> str:
    """Cari atau buat folder di Google Drive, return folder ID."""
    q = f"name='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    if parent_id:
        q += f" and '{parent_id}' in parents"
    results = service.files().list(q=q, fields="files(id)").execute()
    files = results.get("files", [])
    if files:
        return files[0]["id"]

    meta = {"name": name, "mimeType": "application/vnd.google-apps.folder"}
    if parent_id:
        meta["parents"] = [parent_id]
    folder = service.files().create(body=meta, fields="id").execute()
    return folder["id"]


def file_exists_in_drive(service, name: str, folder_id: str) -> bool:
    """Cek apakah file sudah ada di folder Drive."""
    safe = name.replace("'", "\\'")
    q = f"name='{safe}' and '{folder_id}' in parents and trashed=false"
    results = service.files().list(q=q, fields="files(id)").execute()
    return bool(results.get("files"))


def upload_file(service, filepath: Path, filename: str, folder_id: str) -> None:
    """Upload satu file ke Google Drive."""
    safe_name = _sanitize(filename)
    if SKIP_EXISTING and file_exists_in_drive(service, safe_name, folder_id):
        skip(f"Skip (sudah ada): {safe_name}")
        return

    media = MediaFileUpload(str(filepath), resumable=True)
    meta  = {"name": safe_name, "parents": [folder_id]}
    service.files().create(body=meta, media_body=media, fields="id").execute()
    upload(f"Uploaded: {safe_name}")


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

def process_files(files, course, drive, root_id, token, folder_cache):
    total_uploaded = 0
    total_error    = 0
    failed_entries = []

    def cached_folder(name: str, parent_id: str) -> str:
        key = (parent_id, name)
        if key not in folder_cache:
            folder_cache[key] = get_or_create_folder(drive, name, parent_id)
        return folder_cache[key]

    course_folder_id = cached_folder(course["name"], root_id)

    for f in files:
        try:
            section_name = _sanitize(f["section"]) or "Umum"
            module_name  = _sanitize(f["module"])  or None

            section_folder_id = cached_folder(section_name, course_folder_id)
            target_folder_id  = cached_folder(module_name, section_folder_id) if module_name else section_folder_id

            filepath = download_file(f["url"], DOWNLOAD_DIR / course["name"], f["name"])
            if filepath is None:
                warn(f"Tidak bisa download: {f['name']}")
                continue
            upload_file(drive, filepath, f["name"], target_folder_id)
            total_uploaded += 1
            time.sleep(0.3)
        except Exception as e:
            err(f"Gagal: {f['name']} → {e}")
            total_error += 1
            failed_entries.append({"name": f["name"], "course": course["name"]})

    return total_uploaded, total_error, failed_entries


def main():
    retry_mode = "--retry" in sys.argv

    print(f"\n{C.BOLD}{'═'*55}")
    print(f"  📚  Moodle → Google Drive Auto-Sync" + (" [RETRY MODE]" if retry_mode else ""))
    print(f"{'═'*55}{C.RESET}\n")

    if not Path("credentials.json").exists():
        err("File 'credentials.json' tidak ditemukan!")
        print("     → Ikuti langkah setup di README.md terlebih dahulu.")
        return

    info("Login ke Moodle...")
    try:
        token = moodle_get_token()
    except RuntimeError as e:
        err(str(e))
        return
    ok(f"Login berhasil sebagai: {USERNAME}")

    info("Autentikasi Google Drive...")
    drive = authenticate_drive()
    root_id = get_or_create_folder(drive, GDRIVE_FOLDER_NAME)
    ok(f"Google Drive folder siap: '{GDRIVE_FOLDER_NAME}'")

    total_uploaded = 0
    total_error    = 0
    all_failed     = []
    folder_cache: dict[tuple, str] = {}

    if retry_mode:
        if not FAILED_LOG.exists():
            err(f"File '{FAILED_LOG}' tidak ditemukan. Jalankan sync normal dulu.")
            return
        failed = json.loads(FAILED_LOG.read_text())
        # {course: set(name)}
        retry_map: dict[str, set] = {}
        for f in failed:
            retry_map.setdefault(f["course"], set()).add(f["name"])
        info(f"Retry {sum(len(v) for v in retry_map.values())} file dari {len(retry_map)} course...")

        courses = get_enrolled_courses(token)
        for course in courses:
            if course["name"] not in retry_map:
                continue
            targets = retry_map[course["name"]]
            print(f"\n{C.BOLD}📖  {course['name']}{C.RESET}")
            all_files = get_files_from_course(token, course)
            files = [f for f in all_files if f["name"] in targets]
            print(f"     {len(files)} file akan dicoba ulang")
            u, e, bad = process_files(files, course, drive, root_id, token, folder_cache)
            total_uploaded += u; total_error += e; all_failed += bad
    else:
        courses = get_enrolled_courses(token)
        for course in courses:
            print(f"\n{C.BOLD}📖  {course['name']}{C.RESET}")
            files = get_files_from_course(token, course)
            print(f"     {len(files)} file ditemukan")
            if not files:
                continue
            u, e, bad = process_files(files, course, drive, root_id, token, folder_cache)
            total_uploaded += u; total_error += e; all_failed += bad

    if all_failed:
        FAILED_LOG.write_text(json.dumps(all_failed, ensure_ascii=False, indent=2))
        warn(f"{len(all_failed)} file gagal disimpan ke '{FAILED_LOG}' → jalankan: python3 moodle_sync.py --retry")
    elif FAILED_LOG.exists():
        FAILED_LOG.unlink()

    print(f"\n{C.BOLD}{'─'*55}")
    print(f"  Selesai!  ✅ {total_uploaded} file diupload  |  ❌ {total_error} error")
    print(f"{'─'*55}{C.RESET}\n")


if __name__ == "__main__":
    main()
