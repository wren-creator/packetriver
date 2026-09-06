-- Packet River General Store seed. The MariaDB entrypoint created database
-- `generalstore` + user `shop`@`%`; this adds the schema and seed. staff_notes
-- is where the session flag lands (planted by the websites entrypoint); it has
-- no page - only a UNION out of the product search reaches it.

USE generalstore;
SET NAMES utf8mb4;

DROP TABLE IF EXISTS staff_notes;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  username      VARCHAR(64) NOT NULL UNIQUE,
  password_hash CHAR(32) NOT NULL,
  role          ENUM('customer','staff','admin') NOT NULL DEFAULT 'customer',
  created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE products (
  id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255) NOT NULL,
  price DECIMAL(10,2) NOT NULL DEFAULT 0, stock INT NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE staff_notes (id INT AUTO_INCREMENT PRIMARY KEY, note TEXT NOT NULL)
  ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO users (username, password_hash, role) VALUES
  ('shopper', MD5('shopper'), 'customer'),
  ('m_reyes', MD5('Spring2026!'), 'staff');

INSERT INTO products (name, price, stock) VALUES
  ('Bag of Nails, 1lb', 4.25, 120), ('Galvanised Wire, 50ft', 11.90, 34),
  ('Work Gloves, Leather', 17.50, 58), ('Duct Tape, Silver', 6.75, 200),
  ('Lantern Fuel, 1qt', 9.20, 41), ('Fishing Line, 300yd', 8.40, 77),
  ('Rock Salt, 25lb', 7.10, 66), ('Storm Lantern', 28.00, 12),
  ('Canning Jars, dozen', 13.25, 45), ('Bug Spray, Family Size', 10.60, 88),
  ('Charcoal, 8lb', 9.95, 53), ('Rope, 3/8in, 100ft', 22.30, 19);

INSERT INTO staff_notes (note) VALUES ('flag not yet planted');
