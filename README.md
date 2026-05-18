# 📚 Moodle → Google Drive Auto-Sync

Script Python untuk otomatis download semua materi dari Moodle dan upload ke Google Drive.

---

## 📋 Prasyarat

- Python 3.10+
- Akun Google dengan Google Drive API aktif

---

## 🛠️ Setup (Lakukan Sekali)

### Langkah 1 — Install dependencies

```bash
pip install -r requirements.txt
```

### Langkah 2 — Aktifkan Google Drive API

1. Buka [https://console.cloud.google.com](https://console.cloud.google.com)
2. Buat project baru (atau pakai yang sudah ada)
3. Di sidebar kiri → **APIs & Services** → **Library**
4. Cari **"Google Drive API"** → klik **Enable**
5. Pergi ke **APIs & Services** → **Credentials**
6. Klik **+ Create Credentials** → pilih **OAuth client ID**
7. Application type: **Desktop app** → beri nama → klik **Create**
8. Download JSON → **rename jadi `credentials.json`**
9. Taruh file `credentials.json` di folder yang sama dengan `moodle_sync.py`

> ⚠️ Kalau muncul "This app isn't verified", klik **Advanced** → **Go to (unsafe)**  
> Ini wajar untuk OAuth app personal yang belum diverifikasi Google.

### Langkah 3 — Edit konfigurasi di script

Buka `moodle_sync.py`, edit bagian ini:

```python
MOODLE_URL  = "https://elearning.sekolah.ac.id"  # URL Moodle sekolahmu
USERNAME    = "username_kamu"
PASSWORD    = "password_kamu"
GDRIVE_FOLDER_NAME  = "Materi Sekolah"            # Nama folder di Drive
```

---

## ▶️ Cara Pakai

```bash
python3 moodle_sync.py
```

- Pertama kali jalan: browser akan terbuka untuk OAuth Google Drive → izinkan akses
- Token disimpan di `token.pickle` — login berikutnya otomatis tanpa buka browser

---

## 📁 Struktur Folder di Google Drive

```
Materi Sekolah/
├── Pemrograman Web/
│   ├── materi-1.pdf
│   └── tugas-1.docx
├── Basis Data/
│   ├── slides-week1.pptx
│   └── erd-template.pdf
└── ...
```

---

## ⚙️ Opsi Tambahan

| Opsi di script | Default | Keterangan |
|---|---|---|
| `SKIP_EXISTING` | `True` | Skip file yang sudah ada di Drive |
| `DOWNLOAD_DIR` | `./downloads` | Folder lokal sementara sebelum upload |

---

## 🔄 Jalankan Otomatis (Opsional)

### Pakai cron (Linux/Mac) — misalnya tiap hari jam 07.00:

```bash
crontab -e
# Tambahkan baris ini:
0 7 * * * cd /path/ke/folder && python3 moodle_sync.py >> sync.log 2>&1
```

---

## ❓ Troubleshooting

| Error | Solusi |
|---|---|
| `Login gagal` | Cek USERNAME/PASSWORD, pastikan tidak pakai SSO/LDAP eksternal |
| `credentials.json not found` | Pastikan file ada di folder yang sama dengan script |
| `0 course ditemukan` | Moodle mungkin pakai layout custom — coba inspect HTML dashboard untuk pola URL course |
| File tidak terdownload | Resource mungkin tipe `url` (link eksternal), bukan file — ini normal dilewati |
