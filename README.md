# Moodle → Google Drive Auto-Sync

Script Python untuk otomatis download semua materi dari Moodle dan upload ke Google Drive, terorganisir per section dan modul seperti struktur di Moodle.

---

## Prasyarat

- Python 3.10+
- Akun Google dengan Google Drive API aktif
- Akun Moodle yang bisa login via username/password (bukan SSO eksternal)

---

## Setup (Lakukan Sekali)

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Buat credentials.json dari Google Cloud Console

1. Buka [https://console.cloud.google.com](https://console.cloud.google.com)
2. Buat project baru → beri nama (misal: `moodle-sync`)
3. Di sidebar → **APIs & Services** → **Library**
4. Cari **Google Drive API** → klik **Enable**
5. Pergi ke **APIs & Services** → **OAuth consent screen**
   - User Type: **External** → klik Create
   - Isi App name, User support email, Developer contact email → Save
   - Di bagian **Test users** → klik **Add users** → masukkan email Google kamu → Save
6. Pergi ke **APIs & Services** → **Credentials**
   - Klik **+ Create Credentials** → pilih **OAuth client ID**
   - Application type: **Desktop app** → beri nama → klik **Create**
   - Klik **Download JSON** pada credential yang baru dibuat
7. Rename file hasil download menjadi `credentials.json`
8. Taruh `credentials.json` di folder yang sama dengan `moodle_sync.py`

> **Kenapa perlu tambah Test users?**  
> App OAuth yang belum diverifikasi Google hanya bisa dipakai oleh email yang didaftarkan sebagai test user. Kalau dilewati, akan muncul error 403 saat authorize.

### 3. Edit konfigurasi di script

Buka `moodle_sync.py`, edit bagian ini:

```python
MOODLE_URL          = "https://elearning.sekolah.ac.id"  # URL Moodle sekolahmu
USERNAME            = "username_kamu"
PASSWORD            = "password_kamu"
GDRIVE_FOLDER_NAME  = "Materi Sekolah"                   # Nama folder di Drive
```

---

## Cara Pakai

```bash
python3 moodle_sync.py
```

- **Pertama kali**: browser terbuka untuk authorize Google Drive → izinkan akses → token disimpan di `token.pickle`
- **Selanjutnya**: otomatis tanpa buka browser
- **Sync berikutnya**: file yang sudah ada di Drive di-skip, hanya file baru yang diupload

---

## Struktur Folder di Google Drive

Folder dibuat otomatis mengikuti struktur Moodle:

```
Materi Sekolah/
├── Nama Course/
│   ├── Nama Section/
│   │   ├── Nama Modul/
│   │   │   ├── file.pdf
│   │   │   └── materi.pptx
│   │   └── Modul Lain/
│   │       └── tugas.docx
│   └── Section Lain/
│       └── ...
└── Course Lain/
    └── ...
```

---

## Opsi Konfigurasi

| Variabel | Default | Keterangan |
|---|---|---|
| `SKIP_EXISTING` | `True` | Skip file yang sudah ada di Drive (incremental sync) |
| `DOWNLOAD_DIR` | `./downloads` | Folder lokal sementara sebelum upload |

---

## Jalankan Otomatis (Opsional)

Pakai cron (Linux/Mac) — contoh tiap hari jam 07.00:

```bash
crontab -e
# Tambahkan baris ini:
0 7 * * * cd /path/ke/folder && PYTHONUNBUFFERED=1 python3 moodle_sync.py >> sync.log 2>&1
```

---

## Troubleshooting

| Error | Solusi |
|---|---|
| `Login gagal` | Cek USERNAME/PASSWORD. Pastikan login bisa dilakukan via form biasa, bukan SSO/LDAP eksternal |
| `credentials.json not found` | Pastikan file ada di folder yang sama dengan script |
| Error 403 saat OAuth | Tambahkan email Google kamu sebagai Test user di OAuth consent screen (lihat langkah 5 setup) |
| File tidak terdownload | Resource bertipe `url` (link eksternal) atau `forum` memang dilewati — hanya file yang bisa didownload yang disync |
| `token.pickle` expired | Hapus file `token.pickle`, jalankan ulang script, authorize ulang di browser |
