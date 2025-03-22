-- ===========================================
-- Script: setup-passwords.sql
-- Description: Handles user authentication by creating and managing passwords.
-- Includes stored procedures for adding users (sp_add_user), authenticating 
-- users (authenticate), generating salts (make_salt), and changing a password 
-- (sp_change_password).
-- ===========================================

-- ================================
-- DROP EXISTING FUNCTIONS AND PROCEDURES
-- ================================
DROP FUNCTION IF EXISTS make_salt;
DROP FUNCTION IF EXISTS authenticate;
DROP PROCEDURE IF EXISTS sp_add_user;
DROP PROCEDURE IF EXISTS sp_change_password;

-- ================================
-- FUNCTION: make_salt
-- Generates a random 8-character salt for password hashing.
-- ================================
DELIMITER !
CREATE FUNCTION make_salt(num_chars INT)
RETURNS VARCHAR(20) DETERMINISTIC
BEGIN
    DECLARE salt VARCHAR(20) DEFAULT '';

    -- Don't want to generate more than 20 characters of salt.
    SET num_chars = LEAST(20, num_chars);

    -- Generate the salt!  Characters used are ASCII code 32 (space)
    -- through 126 ('z').
    WHILE num_chars > 0 DO
        SET salt = CONCAT(salt, CHAR(32 + FLOOR(RAND() * 95)));
        SET num_chars = num_chars - 1;
    END WHILE;

    RETURN salt;
END !
DELIMITER ;

-- ================================
-- PROCEDURE: sp_add_user
-- Adds a new user with a hashed password and generated salt.
-- ================================
DELIMITER !
CREATE PROCEDURE sp_add_user(new_username VARCHAR(20), password VARCHAR(20))
BEGIN
  DECLARE salt_value CHAR(8);
  DECLARE salted_hashed_password BINARY(64);

  -- Generate an 8-character salt by calling the given function
  SET salt_value = make_salt(8);

  -- Concatenate the salt with the password and hash it using SHA-256
  SET salted_hashed_password = SHA2(CONCAT(salt_value, password), 256);

  -- Insert the new user record into the table
  INSERT INTO users (username, salt, password_hash)
  VALUES (new_username, salt_value, salted_hashed_password);
END !
DELIMITER ;

-- ================================
-- FUNCTION: authenticate
-- Validates user login credentials by checking hashed password.
-- ================================
DELIMITER !
CREATE FUNCTION authenticate(username VARCHAR(20), password VARCHAR(20))
RETURNS TINYINT DETERMINISTIC
BEGIN
  DECLARE stored_salt CHAR(8);
  DECLARE stored_hash BINARY(64);
  DECLARE computed_hash BINARY(64);

  -- Retrieve the salt and stored hash for the given username
  SELECT salt, password_hash INTO stored_salt, stored_hash
  FROM users
  WHERE users.username = username;

  -- If no matching username was found, return 0 (authentication failed)
  IF stored_salt IS NULL THEN
    RETURN 0;
  END IF;

  -- Compute the hash using the stored salt and the provided password
  SET computed_hash = SHA2(CONCAT(stored_salt, password), 256);

  -- Compare the computed hash with the stored hash
  IF computed_hash = stored_hash THEN
    RETURN 1;  -- Authentication successful
  ELSE
    RETURN 0;  -- Authentication failed
  END IF;
END !
DELIMITER ;

-- ================================
-- FUNCTION: sp_change_password
-- Generates a new salt and changes the given user's password to a new given 
-- password (after salting and hashing)
-- ================================
DELIMITER !
CREATE PROCEDURE sp_change_password(
  username VARCHAR(20), new_password VARCHAR(20))
BEGIN
    DECLARE new_salt CHAR(8);
    DECLARE new_hashed_password BINARY(64);

    -- Generate a new salt
    SET new_salt = make_salt(8);

    -- Compute the new salted and hashed password
    SET new_hashed_password = SHA2(CONCAT(new_salt, new_password), 256);

    -- Update the user's password and salt in the users table
    UPDATE users
    SET salt = new_salt, password_hash = new_hashed_password
    WHERE users.username = username;
END !
DELIMITER ;