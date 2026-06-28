-- =============================================================================
-- SmartTex Inventory — MySQL Database Schema
-- Textile & Production Management System
--
-- Usage:
--   mysql -u root -p -e "CREATE DATABASE smarttex_inventory CHARACTER SET utf8mb4;"
--   mysql -u root -p smarttex_inventory < schema.sql
--
-- Note: The Flask app defaults to SQLite for local development (no setup
-- required) and uses this schema automatically via SQLAlchemy when you point
-- DATABASE_URL at a MySQL instance. This file is provided for DBAs who want
-- to provision the schema directly, review structure, or migrate data.
-- =============================================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- -----------------------------------------------------------------------------
-- Users & Roles
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(120) NOT NULL,
    username VARCHAR(64) NOT NULL UNIQUE,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(40) NOT NULL DEFAULT 'Inventory Manager',
    phone VARCHAR(30),
    avatar_url VARCHAR(255),
    is_active_user BOOLEAN DEFAULT TRUE,
    last_login_at DATETIME,
    reset_token VARCHAR(255),
    reset_token_expiry DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_users_username (username),
    INDEX idx_users_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------------------------------
-- Warehouses
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS warehouses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    warehouse_code VARCHAR(30) NOT NULL UNIQUE,
    name VARCHAR(120) NOT NULL,
    location VARCHAR(255),
    capacity_meters FLOAT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    deleted_at DATETIME,
    deleted_by_id INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (deleted_by_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------------------------------
-- Suppliers
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS suppliers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    supplier_code VARCHAR(30) NOT NULL UNIQUE,
    company_name VARCHAR(150) NOT NULL,
    contact_person VARCHAR(100),
    phone VARCHAR(30),
    email VARCHAR(120),
    address VARCHAR(255),
    country VARCHAR(80),
    rating FLOAT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    deleted_at DATETIME,
    deleted_by_id INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (deleted_by_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------------------------------
-- Fabrics (core inventory item)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fabrics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fabric_code VARCHAR(30) NOT NULL UNIQUE,
    name VARCHAR(120) NOT NULL,
    fabric_type VARCHAR(60) NOT NULL,
    gsm INT,
    width_inches FLOAT,
    color VARCHAR(40),
    pattern VARCHAR(60),
    roll_number VARCHAR(40),
    quantity_meters FLOAT NOT NULL DEFAULT 0,
    reserved_meters FLOAT NOT NULL DEFAULT 0,
    damaged_meters FLOAT NOT NULL DEFAULT 0,
    unit_cost FLOAT NOT NULL DEFAULT 0,
    selling_price FLOAT NOT NULL DEFAULT 0,
    low_stock_threshold FLOAT DEFAULT 100,
    warehouse_id INT,
    supplier_id INT,
    qr_code_path VARCHAR(255),
    barcode_path VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    deleted_at DATETIME,
    deleted_by_id INT,
    date_added DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_fabrics_code (fabric_code),
    FOREIGN KEY (warehouse_id) REFERENCES warehouses(id) ON DELETE SET NULL,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE SET NULL,
    FOREIGN KEY (deleted_by_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------------------------------
-- Inventory Movements (audit ledger for every stock change)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS inventory_movements (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fabric_id INT NOT NULL,
    movement_type VARCHAR(20) NOT NULL,  -- IN, OUT, ADJUSTMENT, DAMAGE, TRANSFER, PRODUCTION_USE
    quantity_meters FLOAT NOT NULL,
    reference VARCHAR(120),
    note VARCHAR(255),
    performed_by_id INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_movements_created (created_at),
    FOREIGN KEY (fabric_id) REFERENCES fabrics(id) ON DELETE CASCADE,
    FOREIGN KEY (performed_by_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------------------------------
-- Purchase Orders & Items
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS purchase_orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    po_number VARCHAR(30) NOT NULL UNIQUE,
    supplier_id INT NOT NULL,
    order_date DATE DEFAULT (CURRENT_DATE),
    expected_date DATE,
    delivered_date DATE,
    status VARCHAR(20) DEFAULT 'Pending',  -- Pending, Ordered, Received, Cancelled
    payment_status VARCHAR(20) DEFAULT 'Unpaid',  -- Unpaid, Partial, Paid
    amount_paid FLOAT DEFAULT 0,
    notes VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS purchase_order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    purchase_order_id INT NOT NULL,
    fabric_id INT,
    description VARCHAR(150),
    quantity_meters FLOAT NOT NULL,
    unit_cost FLOAT NOT NULL,
    FOREIGN KEY (purchase_order_id) REFERENCES purchase_orders(id) ON DELETE CASCADE,
    FOREIGN KEY (fabric_id) REFERENCES fabrics(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------------------------------
-- Warehouse Transfers
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS warehouse_transfers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fabric_id INT NOT NULL,
    from_warehouse_id INT NOT NULL,
    to_warehouse_id INT NOT NULL,
    quantity_meters FLOAT NOT NULL,
    transferred_by_id INT,
    note VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (fabric_id) REFERENCES fabrics(id) ON DELETE CASCADE,
    FOREIGN KEY (from_warehouse_id) REFERENCES warehouses(id),
    FOREIGN KEY (to_warehouse_id) REFERENCES warehouses(id),
    FOREIGN KEY (transferred_by_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------------------------------
-- Customers
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS customers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_code VARCHAR(30) NOT NULL UNIQUE,
    name VARCHAR(120) NOT NULL,
    phone VARCHAR(30),
    email VARCHAR(120),
    address VARCHAR(255),
    company_name VARCHAR(150),
    is_active BOOLEAN DEFAULT TRUE,
    deleted_at DATETIME,
    deleted_by_id INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (deleted_by_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------------------------------
-- Sales Orders & Items
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sales_orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    invoice_number VARCHAR(30) NOT NULL UNIQUE,
    customer_id INT NOT NULL,
    order_date DATE DEFAULT (CURRENT_DATE),
    tax_percent FLOAT DEFAULT 0,
    discount_amount FLOAT DEFAULT 0,
    payment_status VARCHAR(20) DEFAULT 'Unpaid',  -- Unpaid, Partial, Paid
    amount_paid FLOAT DEFAULT 0,
    notes VARCHAR(255),
    created_by_id INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS sales_order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sales_order_id INT NOT NULL,
    fabric_id INT NOT NULL,
    quantity_meters FLOAT NOT NULL,
    unit_price FLOAT NOT NULL,
    FOREIGN KEY (sales_order_id) REFERENCES sales_orders(id) ON DELETE CASCADE,
    FOREIGN KEY (fabric_id) REFERENCES fabrics(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------------------------------
-- Production Orders
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS production_orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    production_code VARCHAR(30) NOT NULL UNIQUE,
    product_name VARCHAR(150) NOT NULL,
    fabric_id INT NOT NULL,
    quantity_required_meters FLOAT NOT NULL,
    quantity_used_meters FLOAT DEFAULT 0,
    waste_meters FLOAT DEFAULT 0,
    assigned_team VARCHAR(120),
    start_date DATE DEFAULT (CURRENT_DATE),
    deadline DATE,
    completed_date DATE,
    status VARCHAR(20) DEFAULT 'Pending',  -- Pending, Approved, In Progress, Completed, Delayed
    notes VARCHAR(255),
    created_by_id INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (fabric_id) REFERENCES fabrics(id),
    FOREIGN KEY (created_by_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------------------------------
-- Workers, Attendance, Payroll
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS workers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    worker_code VARCHAR(30) NOT NULL UNIQUE,
    name VARCHAR(120) NOT NULL,
    cnic VARCHAR(20),
    phone VARCHAR(30),
    department VARCHAR(80),
    designation VARCHAR(80),
    base_salary FLOAT NOT NULL DEFAULT 0,
    date_joined DATE DEFAULT (CURRENT_DATE),
    is_active BOOLEAN DEFAULT TRUE,
    deleted_at DATETIME,
    deleted_by_id INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (deleted_by_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    worker_id INT NOT NULL,
    date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'Present',  -- Present, Absent, Half-Day, Leave
    hours_worked FLOAT DEFAULT 8,
    overtime_hours FLOAT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_worker_date (worker_id, date),
    FOREIGN KEY (worker_id) REFERENCES workers(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS payroll (
    id INT AUTO_INCREMENT PRIMARY KEY,
    worker_id INT NOT NULL,
    month VARCHAR(7) NOT NULL,  -- 'YYYY-MM'
    base_salary FLOAT NOT NULL,
    overtime_pay FLOAT DEFAULT 0,
    deductions FLOAT DEFAULT 0,
    bonus FLOAT DEFAULT 0,
    net_pay FLOAT NOT NULL,
    is_paid BOOLEAN DEFAULT FALSE,
    paid_date DATE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_worker_month (worker_id, month),
    FOREIGN KEY (worker_id) REFERENCES workers(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------------------------------
-- Notifications
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    category VARCHAR(30) NOT NULL DEFAULT 'system',
    title VARCHAR(150) NOT NULL,
    message VARCHAR(500),
    link VARCHAR(255),
    is_read BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_notifications_created (created_at),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------------------------------
-- Audit Logs
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS audit_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    action VARCHAR(50) NOT NULL,    -- CREATE, UPDATE, DELETE, LOGIN, LOGOUT
    module VARCHAR(50) NOT NULL,    -- Fabric, Supplier, Sales, Production, Auth, etc.
    entity_id INT,
    description VARCHAR(500),
    ip_address VARCHAR(64),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_audit_created (created_at),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------------------------------
-- Messages (Team Chat — shared channel visible to all authenticated users)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    body VARCHAR(2000) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_messages_created (created_at),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SET FOREIGN_KEY_CHECKS = 1;

-- =============================================================================
-- Seed an initial Admin user (username: admin / password: admin123)
-- CHANGE THIS PASSWORD IMMEDIATELY after first login in a production system.
-- Hash format is Werkzeug's scrypt (Flask-Login compatible). To generate your
-- own for a different password:
--   python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('your-password'))"
-- =============================================================================
INSERT INTO users (full_name, username, email, password_hash, role)
VALUES (
    'System Administrator',
    'admin',
    'admin@smarttex.com',
    'scrypt:32768:8:1$LaObtEl85WZD8yVD$8fae8e85329f49c30f5ffc39ab00dd86d49a79e0982bfbba200b7413e6d7afb804b54b49a063c1cf75b0e97e7b1b5a15d60589fc4302b7741c2cb7d2a7a350e8',
    'Admin'
);
