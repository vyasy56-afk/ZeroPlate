-- ZeroPlate: MySQL Production Database Schema
-- Project: ZeroPlate - AI-Powered Demand Forecasting and Surplus Redistribution
-- Author: Yogesh Vyas · BCA (AI & DS) · Graphic Era (Deemed to be University)

CREATE DATABASE IF NOT EXISTS zeroplate_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE zeroplate_db;

CREATE TABLE IF NOT EXISTS menu_items (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(150) NOT NULL,
    category VARCHAR(80) NOT NULL,
    meal_type ENUM('Breakfast', 'Lunch', 'Snacks', 'Dinner') NOT NULL,
    base_price DECIMAL(8,2) NOT NULL,
    prep_cost DECIMAL(8,2) NOT NULL,
    shelf_life_hours INT NOT NULL DEFAULT 6,
    image_emoji VARCHAR(20) DEFAULT '🍲',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS daily_plans (
    id INT PRIMARY KEY AUTO_INCREMENT,
    date DATE NOT NULL,
    item_id INT NOT NULL,
    predicted_demand INT NOT NULL,
    recommended_cook_qty INT NOT NULL,
    actual_prepared_qty INT NOT NULL,
    actual_sold_qty INT NOT NULL DEFAULT 0,
    status ENUM('PLANNED', 'COOKING', 'IN_SERVICE', 'SURPLUS_DETECTED', 'CLOSED') NOT NULL DEFAULT 'IN_SERVICE',
    safety_buffer INT NOT NULL DEFAULT 0,
    threshold_surplus INT NOT NULL DEFAULT 8,
    closing_time TIME NOT NULL DEFAULT '20:30:00',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (item_id) REFERENCES menu_items(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS marketplace_items (
    id INT PRIMARY KEY AUTO_INCREMENT,
    daily_plan_id INT NOT NULL,
    title VARCHAR(150) NOT NULL,
    description TEXT,
    original_price DECIMAL(8,2) NOT NULL,
    discounted_price DECIMAL(8,2) NOT NULL,
    discount_pct INT NOT NULL,
    quantity_listed INT NOT NULL,
    quantity_claimed INT NOT NULL DEFAULT 0,
    status ENUM('ACTIVE', 'SOLD_OUT', 'EXPIRED_TO_NGO') NOT NULL DEFAULT 'ACTIVE',
    listed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    pickup_until TIME NOT NULL,
    FOREIGN KEY (daily_plan_id) REFERENCES daily_plans(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS marketplace_orders (
    id INT PRIMARY KEY AUTO_INCREMENT,
    marketplace_item_id INT NOT NULL,
    student_name VARCHAR(120) NOT NULL,
    student_id_roll VARCHAR(50) NOT NULL,
    quantity INT NOT NULL,
    total_price DECIMAL(8,2) NOT NULL,
    token_code VARCHAR(32) NOT NULL UNIQUE,
    status ENUM('RESERVED', 'COLLECTED', 'CANCELLED') NOT NULL DEFAULT 'RESERVED',
    ordered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    collected_at TIMESTAMP NULL,
    FOREIGN KEY (marketplace_item_id) REFERENCES marketplace_items(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS ngos (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(180) NOT NULL,
    registration_no VARCHAR(80) NOT NULL,
    contact_person VARCHAR(120) NOT NULL,
    phone VARCHAR(30) NOT NULL,
    email VARCHAR(120) NOT NULL,
    address TEXT NOT NULL,
    verified TINYINT(1) NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS ngo_donations (
    id INT PRIMARY KEY AUTO_INCREMENT,
    daily_plan_id INT NULL,
    item_name VARCHAR(150) NOT NULL,
    portions INT NOT NULL,
    ngo_id INT NULL,
    pickup_window_deadline DATETIME NOT NULL,
    status ENUM('PENDING_CLAIM', 'CLAIMED', 'COLLECTED', 'EXPIRED_TO_COMPOST') NOT NULL DEFAULT 'PENDING_CLAIM',
    dispatched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    claimed_at TIMESTAMP NULL,
    collected_at TIMESTAMP NULL,
    verification_pin VARCHAR(10) NULL,
    notes TEXT,
    FOREIGN KEY (daily_plan_id) REFERENCES daily_plans(id) ON DELETE SET NULL,
    FOREIGN KEY (ngo_id) REFERENCES ngos(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS composting_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    daily_plan_id INT NULL,
    item_name VARCHAR(150) NOT NULL,
    weight_kg DECIMAL(8,2) NOT NULL,
    source_reason VARCHAR(100) NOT NULL,
    facility_partner VARCHAR(180) NOT NULL,
    estimated_compost_kg DECIMAL(8,2) NOT NULL,
    co2_diverted_kg DECIMAL(8,2) NOT NULL,
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    batch_code VARCHAR(50) NOT NULL
);
