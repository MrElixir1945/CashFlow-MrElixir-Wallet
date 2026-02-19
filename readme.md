# 💳 CashFlow — Personal Finance Manager

> Aplikasi manajemen keuangan pribadi dengan dua antarmuka: **Bot Telegram** untuk input cepat dan **Web Dashboard** untuk visualisasi data — bisa diakses dari mana saja via internet.

![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python) ![Flask](https://img.shields.io/badge/Flask-Web%20Framework-black?logo=flask) ![SQLite](https://img.shields.io/badge/Database-SQLite-blue?logo=sqlite) ![Tailscale](https://img.shields.io/badge/Network-Tailscale-orange) ![Platform](https://img.shields.io/badge/Server-Proxmox%20VE-red) ![License](https://img.shields.io/badge/License-MIT-green)

---

## 💡 Konsep

Project ini lahir dari kebutuhan mencatat pengeluaran harian dengan cepat tanpa buka aplikasi berat. Cukup chat ke bot Telegram, saldo langsung terupdate. Dashboard web bisa dibuka kapan saja dari HP maupun laptop tanpa perlu VPN atau berada di jaringan rumah.

---

## 🏗️ Arsitektur Sistem

```
[Telegram User]
      │
      │ Chat: "50.000 : Makan siang"
      ▼
[Bot Telegram - bot.py]
      │
      │ INSERT/DELETE
      ▼
[SQLite - finance.db] ◄──────────────────────┐
                                              │ SELECT
                                    [Web Dashboard - app.py]
                                              │
                                              │ HTTPS (Public)
                                    [Tailscale Funnel]
                                              │
                                    [Browser User - HP/Laptop]
```

---

## ✨ Fitur

### 🤖 Telegram Bot
- 📥 **Input Pemasukan** — Format: `Nominal : Keterangan`
- 📤 **Input Pengeluaran** — Format: `Nominal : Keterangan`
- 💰 **Saldo Real-time** — Ditampilkan otomatis setiap buka menu
- 🔗 **Link Dashboard** — Tombol langsung ke web dashboard
- 🔒 **Security** — Hanya User ID yang terdaftar yang bisa akses

### 🌐 Web Dashboard
- 📊 **Total Saldo, Pemasukan & Pengeluaran**
- 📋 **Riwayat Transaksi** lengkap dengan indikator ⬆️ hijau / ⬇️ merah
- ✏️ **Edit Transaksi** langsung dari web (dilindungi password)
- 🗑️ **Hapus Transaksi** langsung dari web (dilindungi password)
- 🌙 **Dark Mode** — UI Glassmorphism yang nyaman di mata

---

## 🛠️ Tech Stack

| Komponen | Detail |
|---|---|
| Bahasa | Python 3 |
| Bot Framework | `pyTelegramBotAPI` (telebot) |
| Web Framework | Flask |
| Database | SQLite (`finance.db`) — shared antara bot & web |
| Frontend | HTML5, CSS Dark Mode, FontAwesome |
| Network | Tailscale Funnel (Public HTTPS tanpa port forwarding) |
| Server | Proxmox VE (LXC Container Ubuntu) |
| Process Manager | Systemd (`money-bot.service` & `money-web.service`) |

---

## 🚀 Cara Deploy

### Prerequisites
```bash
apt update
apt install python3 python3-pip python3-venv -y
```

### 1. Clone repo
```bash
git clone https://github.com/MrElixir1945/CashFlow.git
cd CashFlow
```

### 2. Buat virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Konfigurasi `.env`
```bash
cp .env.example .env
nano .env
```

Isi file `.env`:
```env
TELEGRAM_TOKEN=token_bot_telegram_kamu
ALLOWED_USER_ID=user_id_telegram_kamu
ADMIN_PASSWORD=password_untuk_edit_di_web
PUBLIC_URL=https://domain-kamu.ts.net
```

> 💡 Cara dapat `ALLOWED_USER_ID`: chat ke @userinfobot di Telegram

### 4. Jalankan Bot & Web Server

**Manual (untuk testing):**
```bash
# Terminal 1 - Bot
python bot.py

# Terminal 2 - Web Server
python app.py
```

**Production (via Systemd):**
```bash
# Lihat contoh konfigurasi di bagian Systemd di bawah
```

---

## 🌐 Setup Tailscale Funnel (Akses Public HTTPS)

Tailscale Funnel memungkinkan web dashboard lo diakses dari internet tanpa port forwarding atau VPS. Gratis dan sangat mudah.

### Langkah 1: Install Tailscale
```bash
curl -fsSL https://tailscale.com/install.sh | sh
```

### Langkah 2: Login & Connect
```bash
tailscale up
# Akan muncul link, buka di browser dan login dengan akun Google/GitHub
```

### Langkah 3: Aktifkan Funnel
```bash
# Expose port 5000 (Flask) ke internet dengan HTTPS otomatis
tailscale funnel 5000
```

### Langkah 4: Cek Domain Kamu
```bash
tailscale status
# Domain kamu format: https://nama-mesin.nama-akun.ts.net
```

Setelah ini, web dashboard lo bisa diakses dari mana saja via:
```
https://nama-mesin.nama-akun.ts.net/dashboard?uid=USER_ID_KAMU
```

> ⚠️ **Catatan:** Tailscale Funnel butuh akun Tailscale gratis. Pastikan LXC Container di Proxmox sudah diaktifkan TUN device (`lxc.cgroup2.devices.allow: c 10:200 rwm` dan `lxc.mount.entry: /dev/net/tun dev/net/tun none bind,create=file`).

---

## ⚙️ Setup Systemd (Auto-start Production)

Buat 2 service file agar bot dan web otomatis jalan saat server restart.

### Bot Service
```bash
nano /etc/systemd/system/cashflow-bot.service
```
```ini
[Unit]
Description=CashFlow Telegram Bot
After=network.target

[Service]
WorkingDirectory=/root/money-bot
ExecStart=/root/money-bot/venv/bin/python bot.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### Web Service
```bash
nano /etc/systemd/system/cashflow-web.service
```
```ini
[Unit]
Description=CashFlow Web Dashboard
After=network.target

[Service]
WorkingDirectory=/root/money-bot
ExecStart=/root/money-bot/venv/bin/python app.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### Aktifkan Service
```bash
systemctl daemon-reload
systemctl enable cashflow-bot cashflow-web
systemctl start cashflow-bot cashflow-web

# Cek status
systemctl status cashflow-bot
systemctl status cashflow-web
```

---

## 📁 Struktur Project

```
CashFlow/
├── bot.py                    # Telegram Bot (input transaksi)
├── app.py                    # Flask Web Server (dashboard)
├── templates/
│   └── dashboard.html        # UI Web Dashboard
├── .env.example              # Template konfigurasi
├── requirements.txt          # Python dependencies
└── finance.db                # Auto-generated: database SQLite
```

---

## 📋 Contoh Penggunaan

### Via Telegram
```
User:   /start
Bot:    💳 CASHFLOW
        Saldo Saat Ini: Rp 250.000

        [Pemasukan 📥] [Pengeluaran 📤]
        [📊 Buka Dashboard]

User:   klik [Pengeluaran 📤]
Bot:    📤 PENGELUARAN
        Format: Nominal : Keterangan
        Contoh: 50.000 : Makan

User:   25.000 : Kopi
Bot:    ✅ Sukses: Rp 25.000 - Kopi
        → Saldo otomatis terupdate
```

### Via Web Dashboard
```
Buka: https://domain-kamu.ts.net/dashboard?uid=USER_ID
→ Lihat saldo, pemasukan, pengeluaran
→ Klik ikon pensil untuk edit/hapus transaksi
→ Masukkan admin password
→ Edit atau hapus transaksi langsung
```

---

## 🔒 Keamanan

- **Bot:** Middleware `ALLOWED_USER_ID` — hanya 1 user yang bisa akses
- **Web Edit/Hapus:** Dilindungi `ADMIN_PASSWORD` via modal JavaScript
- **Database:** Tidak pernah diupload ke repository (`.gitignore`)
- **Secrets:** Semua credentials di `.env` yang tidak diupload

---

## 👤 Author

**Mr. Elixir** — [@MrElixir1945](https://github.com/MrElixir1945)

*Self-hosted on Proxmox VE Home Server*
