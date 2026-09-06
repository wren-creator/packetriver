-- The other Main Street storefronts. One schema each, `shop`@`%` granted on it.
-- Flags that live in a DB row (hardware.receipts, pharmacy.patient_records) are
-- planted by the websites entrypoint after boot.

SET NAMES utf8mb4;

-- ============================================================ hardware
CREATE DATABASE IF NOT EXISTS hardware;
GRANT ALL PRIVILEGES ON hardware.* TO 'shop'@'%';
USE hardware;
CREATE TABLE users (id INT AUTO_INCREMENT PRIMARY KEY, username VARCHAR(64) UNIQUE NOT NULL,
  password_hash CHAR(32) NOT NULL, role ENUM('customer','staff','admin') DEFAULT 'customer');
CREATE TABLE products (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255) NOT NULL,
  price DECIMAL(10,2) DEFAULT 0, stock INT DEFAULT 0);
CREATE TABLE receipts (id INT AUTO_INCREMENT PRIMARY KEY, customer VARCHAR(64) NOT NULL,
  total DECIMAL(10,2) DEFAULT 0, notes TEXT);
ALTER TABLE receipts AUTO_INCREMENT = 1001;
INSERT INTO users (username, password_hash) VALUES ('shopper', MD5('shopper'));
INSERT INTO products (name, price, stock) VALUES
  ('PVC Elbow, 1in', 1.40, 300), ('Copper Pipe, 10ft', 24.00, 22),
  ('Lockpick Set (hobby)', 19.99, 8), ('Spool of 12AWG, 100ft', 41.00, 15),
  ('Padlock, brass', 9.50, 60), ('Wire Strippers', 14.25, 30),
  ('Zip Ties, 200ct', 6.00, 140), ('Flashlight, LED', 17.75, 44);
INSERT INTO receipts (customer, total, notes) VALUES
  ('shopper', 21.39, 'PVC + ties, paid cash'),
  ('t_okafor', 41.00, 'wire spool, net-30'),
  ('shopper', 9.50, 'padlock'),
  ('r_singh', 199.99, 'contractor account - see back office'),
  ('shopper', 6.00, 'zip ties'),
  ('flag_holder', 0.00, 'flag not yet planted');

-- ============================================================ pharmacy
CREATE DATABASE IF NOT EXISTS pharmacy;
GRANT ALL PRIVILEGES ON pharmacy.* TO 'shop'@'%';
USE pharmacy;
CREATE TABLE users (id INT AUTO_INCREMENT PRIMARY KEY, username VARCHAR(64) UNIQUE NOT NULL,
  password_hash CHAR(32) NOT NULL, role ENUM('customer','staff','admin') DEFAULT 'customer');
CREATE TABLE products (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255) NOT NULL,
  price DECIMAL(10,2) DEFAULT 0, stock INT DEFAULT 0);
CREATE TABLE patient_records (id INT AUTO_INCREMENT PRIMARY KEY, patient VARCHAR(120) NOT NULL,
  rx VARCHAR(120) NOT NULL, note TEXT);
INSERT INTO users (username, password_hash, role) VALUES
  ('shopper', MD5('shopper'), 'customer'),
  ('a.finch', MD5('Dispense2025!'), 'staff');
INSERT INTO products (name, price, stock) VALUES
  ('Ibuprofen 200mg, 100ct', 8.99, 90), ('Bandages, assorted', 4.50, 120),
  ('Sunscreen SPF50', 11.25, 60), ('Cough Syrup', 7.80, 40),
  ('Reading Glasses +1.5', 15.00, 25), ('Thermometer, digital', 12.40, 33);
INSERT INTO patient_records (patient, rx, note) VALUES
  ('J. Alvarez', 'lisinopril 10mg', 'refill monthly'),
  ('P. Nowak', 'metformin 500mg', '90-day supply'),
  ('K. Osei', 'albuterol HFA', 'spacer provided'),
  ('records audit', 'n/a', 'flag not yet planted');

-- ============================================================ diner
CREATE DATABASE IF NOT EXISTS diner;
GRANT ALL PRIVILEGES ON diner.* TO 'shop'@'%';
USE diner;
CREATE TABLE users (id INT AUTO_INCREMENT PRIMARY KEY, username VARCHAR(64) UNIQUE NOT NULL,
  password_hash CHAR(32) NOT NULL, role ENUM('customer','staff','admin') DEFAULT 'customer');
CREATE TABLE products (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255) NOT NULL,
  price DECIMAL(10,2) DEFAULT 0, stock INT DEFAULT 0);
INSERT INTO users (username, password_hash) VALUES ('shopper', MD5('shopper'));
INSERT INTO products (name, price, stock) VALUES
  ('Bottomless Coffee', 2.25, 999), ('Slice of Pie', 3.75, 20),
  ('Grilled Cheese', 5.50, 40), ('Blue Plate Special', 9.95, 30),
  ('Milkshake', 4.25, 25), ('Short Stack', 6.00, 35);

-- ============================================================ barber
CREATE DATABASE IF NOT EXISTS barber;
GRANT ALL PRIVILEGES ON barber.* TO 'shop'@'%';
USE barber;
CREATE TABLE users (id INT AUTO_INCREMENT PRIMARY KEY, username VARCHAR(64) UNIQUE NOT NULL,
  password_hash CHAR(32) NOT NULL, role ENUM('customer','staff','admin') DEFAULT 'customer');
CREATE TABLE bookings (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(120) NOT NULL,
  note TEXT, bot_note TEXT NULL, created DATETIME NOT NULL);
INSERT INTO users (username, password_hash) VALUES ('shopper', MD5('shopper'));
INSERT INTO bookings (name, note, bot_note, created) VALUES
  ('Walk-in', 'usual', 'reviewed - looks fine', NOW());

-- ============================================================ tavern
CREATE DATABASE IF NOT EXISTS tavern;
GRANT ALL PRIVILEGES ON tavern.* TO 'shop'@'%';
USE tavern;
CREATE TABLE users (id INT AUTO_INCREMENT PRIMARY KEY, username VARCHAR(64) UNIQUE NOT NULL,
  password_hash CHAR(32) NOT NULL, role ENUM('customer','staff','admin') DEFAULT 'customer');
CREATE TABLE products (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255) NOT NULL,
  price DECIMAL(10,2) DEFAULT 0, stock INT DEFAULT 0);
INSERT INTO users (username, password_hash, role) VALUES
  ('shopper', MD5('shopper'), 'customer'),
  ('admin', MD5('admin'), 'admin');
INSERT INTO products (name, price, stock) VALUES
  ('Draft, pint', 5.00, 999), ('Well Whiskey', 6.00, 200),
  ('Basket of Fries', 4.50, 50), ('Jukebox Credit', 1.00, 999);

-- ============================================================ drycleaner
CREATE DATABASE IF NOT EXISTS drycleaner;
GRANT ALL PRIVILEGES ON drycleaner.* TO 'shop'@'%';
USE drycleaner;
CREATE TABLE users (id INT AUTO_INCREMENT PRIMARY KEY, username VARCHAR(64) UNIQUE NOT NULL,
  password_hash CHAR(32) NOT NULL, role ENUM('customer','staff','admin') DEFAULT 'customer');
CREATE TABLE products (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255) NOT NULL,
  price DECIMAL(10,2) DEFAULT 0, stock INT DEFAULT 0);
INSERT INTO users (username, password_hash) VALUES ('shopper', MD5('shopper'));
INSERT INTO products (name, price, stock) VALUES
  ('Shirt, laundered', 2.50, 999), ('Suit, dry cleaned', 14.00, 999),
  ('Dress, dry cleaned', 12.00, 999), ('Alterations, hem', 8.00, 999);

-- ============================================================ baittackle
CREATE DATABASE IF NOT EXISTS baittackle;
GRANT ALL PRIVILEGES ON baittackle.* TO 'shop'@'%';
USE baittackle;
CREATE TABLE users (id INT AUTO_INCREMENT PRIMARY KEY, username VARCHAR(64) UNIQUE NOT NULL,
  password_hash CHAR(32) NOT NULL, role ENUM('customer','staff','admin') DEFAULT 'customer');
CREATE TABLE products (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255) NOT NULL,
  price DECIMAL(10,2) DEFAULT 0, stock INT DEFAULT 0);
INSERT INTO users (username, password_hash) VALUES ('shopper', MD5('shopper'));
INSERT INTO products (name, price, stock) VALUES
  ('Nightcrawlers, dozen', 3.50, 200), ('Bobber, 3-pack', 2.75, 80),
  ('Inner Tube', 18.00, 24), ('Sunscreen SPF30', 9.50, 40),
  ('Rod & Reel Combo', 44.99, 10), ('Tackle Box', 21.00, 15);

FLUSH PRIVILEGES;
