"""
SmartTex Inventory - Configuration
Supports SQLite (default, dev) and MySQL (production) via DATABASE_URL env var.
"""
import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "smarttex-dev-secret-key-change-in-production-9f8a7d6c5b4e")

    # --- Database ---
    # For MySQL in production, set DATABASE_URL like:
    # mysql+pymysql://user:password@localhost:3306/smarttex_inventory
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'smarttex.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    # --- Session / Security ---
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    WTF_CSRF_ENABLED = True

    # --- Uploads ---
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "app", "static", "uploads")
    QRCODE_FOLDER = os.path.join(UPLOAD_FOLDER, "qrcodes")
    BARCODE_FOLDER = os.path.join(UPLOAD_FOLDER, "barcodes")
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB

    # --- Pagination ---
    ITEMS_PER_PAGE = 12

    # --- Business rules ---
    LOW_STOCK_THRESHOLD_METERS = 100  # default low-stock alert threshold
    CURRENCY_SYMBOL = "Rs."

    # --- AI ---
    AI_MIN_DATA_POINTS = 5  # minimum historical points before trusting ML forecast
