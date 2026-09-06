-- Town Hall. Police and Fire need no schema (their bugs are a served file and
-- default creds). Flags that live in a row are planted by the websites
-- entrypoint.

SET NAMES utf8mb4;

CREATE DATABASE IF NOT EXISTS townhall;
GRANT ALL PRIVILEGES ON townhall.* TO 'shop'@'%';
USE townhall;

CREATE TABLE announce (
  id INT AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(160) NOT NULL,
  body  TEXT NOT NULL,             -- rendered raw on the public board
  created DATETIME NOT NULL
);
CREATE TABLE announce_admin (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(64) NOT NULL,
  password_hash CHAR(32) NOT NULL,
  confirm_code VARCHAR(128) NOT NULL
);
CREATE TABLE payroll_users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(64) NOT NULL,
  password_hash CHAR(32) NOT NULL
);

INSERT INTO announce (title, body, created) VALUES
  ('Founder''s Day', 'Parade steps off Saturday at 10am on Main Street.', NOW()),
  ('Water main work', 'Crews on Packet River Rd through Thursday. Expect delays.', NOW());
INSERT INTO announce_admin (username, password_hash, confirm_code) VALUES
  ('clerk', MD5('clerk'), 'confirm-code-not-yet-planted');
INSERT INTO payroll_users (username, password_hash) VALUES
  ('p_ellis', MD5('Payroll!2026'));

FLUSH PRIVILEGES;
