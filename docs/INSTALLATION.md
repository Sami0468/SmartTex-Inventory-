# Installation Guide

## Prerequisites

- Python 3.10+ (developed and tested on 3.12)
- pip
- (Optional, for production) MySQL Server 8.0+

---

## 1. Local Development Setup (SQLite — recommended for getting started)

```bash
cd smartex-inventory

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate          # On Windows: venv\Scripts\activate

# Install all dependencies
pip install -r requirements.txt

# Create the database tables
flask --app run.py init-db

# Load realistic demo data (recommended — populates every module,
# including enough history for the AI forecasting features to run)
flask --app run.py seed-db

# Start the development server
python run.py
```

The app will be available at **http://127.0.0.1:5000**.

Demo accounts created by the seed script:

| Username | Password | Role |
|---|---|---|
| `admin` | `admin123` | Admin |
| `inventory` | `admin123` | Inventory Manager |
| `production` | `admin123` | Production Manager |
| `sales` | `admin123` | Sales Manager |

---

## 2. Production Setup with MySQL

### Step 1 — Create the database

```bash
mysql -u root -p
```

```sql
CREATE DATABASE smarttex_inventory CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'smarttex_user'@'localhost' IDENTIFIED BY 'choose-a-strong-password';
GRANT ALL PRIVILEGES ON smarttex_inventory.* TO 'smarttex_user'@'localhost';
FLUSH PRIVILEGES;
```

### Step 2 — Install the MySQL driver

```bash
pip install PyMySQL
```

(Already listed, commented out, in `requirements.txt` — just uncomment it.)

### Step 3 — Configure environment variables

Copy `.env.example` to `.env` and set:

```bash
SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_hex(32))">
DATABASE_URL=mysql+pymysql://smarttex_user:your_password@localhost:3306/smarttex_inventory
```

Flask reads `DATABASE_URL` automatically via `app/config.py` — no code changes needed.

### Step 4 — Provision the schema

Either let SQLAlchemy create tables automatically:

```bash
flask --app run.py init-db
```

...or apply the hand-written schema directly (useful if your DBA wants to review/adjust it first):

```bash
mysql -u smarttex_user -p smarttex_inventory < sql/schema.sql
```

Both approaches produce the same 17 tables; `sql/schema.sql` additionally seeds a ready-to-use Admin account (`admin` / `admin123` — **change immediately**).

### Step 5 — Run with a production WSGI server

The Flask dev server (`python run.py`) is for development only. For production:

```bash
pip install gunicorn   # already in requirements.txt
gunicorn -w 4 -b 0.0.0.0:8000 run:app
```

Put this behind Nginx or another reverse proxy with HTTPS termination.

---

## 3. Folder Permissions

The app writes generated QR codes and barcodes to:

```
app/static/uploads/qrcodes/
app/static/uploads/barcodes/
```

Ensure the application user has write access to these directories.

---

## 4. Common Issues

**"sqlite3.OperationalError: no such table"**
→ Run `flask --app run.py init-db` before starting the server.

**Barcode generation fails for certain fabric codes**
→ Code128 barcodes only support a specific character set. The app's auto-generated codes (e.g. `FB-0001`) are always compatible; this would only affect manually edited codes with unusual characters.

**Charts not rendering**
→ The dashboard and AI Insights pages use a self-hosted copy of Chart.js (`app/static/js/chart.umd.min.js`) specifically so the app works without external CDN access — useful on locked-down factory networks. If you've modified `base.html`, make sure that script tag wasn't removed.

**Google Fonts not loading**
→ The app references Fraunces, Inter, and JetBrains Mono via Google Fonts CDN for typography polish, but every font has a system-font fallback defined in `main.css`, so the app remains fully usable on networks that block external font CDNs.
