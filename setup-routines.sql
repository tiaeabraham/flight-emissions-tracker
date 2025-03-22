-- ===========================================
-- Script: setup-routines.sql
-- Description: Contains all user-triggered functions, procedures, and triggers.
-- Includes trip emissions calculation, location validation, trip insertion, 
-- and retrieval functions.
-- ===========================================

-- ================================
-- DROP EXISTING FUNCTIONS and PROCEDURES
-- ================================
DROP FUNCTION IF EXISTS get_airport_id;
DROP FUNCTION IF EXISTS calculate_trip_emissions;
DROP FUNCTION IF EXISTS get_trip_distance;
DROP PROCEDURE IF EXISTS sp_add_trip;
DROP Trigger IF EXISTS before_insert_trip;

-- ================================
-- FUNCTION: get_airport_id
-- Retrieves airport_id for a given city and country.
-- ================================
DELIMITER !
CREATE FUNCTION get_airport_id(
  p_city VARCHAR(100), 
  p_country VARCHAR(100)) RETURNS CHAR(3) DETERMINISTIC
BEGIN
  DECLARE airport_code CHAR(3);
  SELECT airport_id INTO airport_code FROM airports
  WHERE city = p_city AND country_id = p_country LIMIT 1;
  RETURN airport_code;
END !
DELIMITER ;

-- ================================
-- FUNCTION: calculate_trip_emissions
-- Computes total CO2 emissions for a given trip based on distance and aircraft 
-- efficiency.
-- ================================
DELIMITER !
CREATE FUNCTION calculate_trip_emissions(
    p_distance_mi FLOAT,
    p_emissions_per_mi FLOAT,
    p_num_passengers INT
) RETURNS FLOAT
DETERMINISTIC
BEGIN
    RETURN p_distance_mi * p_emissions_per_mi * p_num_passengers;
END !
DELIMITER ;

-- ================================
-- FUNCTION: get_trip_distance
-- Retrieves the precomputed distance between two airports from the 
-- distance_view.
-- ================================
DELIMITER !
CREATE FUNCTION get_trip_distance(
    p_from_airport_id CHAR(3),
    p_to_airport_id CHAR(3)
) RETURNS FLOAT
DETERMINISTIC
BEGIN
    DECLARE trip_distance FLOAT;
    SELECT distance_mi INTO trip_distance FROM distance_view
    WHERE from_airport_id = p_from_airport_id 
      AND to_airport_id = p_to_airport_id;
    RETURN trip_distance;
END !
DELIMITER ;

-- ================================
-- PROCEDURE: sp_add_trip
-- Inserts a new trip record, calculates emissions, and stores in the trips 
-- table.
-- ================================
DELIMITER !
CREATE PROCEDURE sp_add_trip(
    IN p_user_id INT,
    IN p_from_airport_id CHAR(3),
    IN p_to_airport_id CHAR(3),
    IN p_departure_date DATE,
    IN p_num_passengers INT
)
BEGIN
    DECLARE p_trip_distance FLOAT;
    DECLARE p_emissions_per_mi FLOAT;
    DECLARE p_total_emissions FLOAT;
    DECLARE p_aircraft_id CHAR(3);
    
    -- Get distance between airports
    SET p_trip_distance = get_trip_distance(p_from_airport_id, p_to_airport_id);
    
    -- Get aircraft emissions per mile
    SELECT aircraft_id INTO p_aircraft_id FROM routes 
    WHERE from_airport_id = p_from_airport_id AND to_airport_id = p_to_airport_id
    LIMIT 1;
    
    SELECT a.emissions_per_mi INTO p_emissions_per_mi 
    FROM aircrafts a
    WHERE a.aircraft_id = (
      SELECT aircraft_id FROM routes WHERE from_airport_id = p_from_airport_id AND to_airport_id = p_to_airport_id
    );
    
    -- Calculate total emissions
    SET p_total_emissions = calculate_trip_emissions(
      p_trip_distance, p_emissions_per_mi, p_num_passengers);

    -- Insert trip record with calculated emissions
    INSERT INTO trips (user_id, from_airport_id, to_airport_id, departure_date, 
      num_passengers, total_emissions)
    VALUES (p_user_id, p_from_airport_id, p_to_airport_id, p_departure_date, 
      p_num_passengers, p_total_emissions);
END !
DELIMITER ;

-- ================================
-- TRIGGER: before_insert_trip
-- When a trip record is about to be inserted, figures out trip_id by fetching 
-- a user's last inputted trip_id, and sets the trip_id to the next available 
-- one.
-- ================================
DELIMITER !
CREATE TRIGGER before_insert_trip
BEFORE INSERT ON trips
FOR EACH ROW
BEGIN
    DECLARE next_trip_id INT;
    
    -- Get the next available trip_id for this user
    SELECT COALESCE(MAX(trip_id) + 1, 1) INTO next_trip_id 
    FROM trips WHERE user_id = NEW.user_id;
    
    -- Assign the computed trip_id
    SET NEW.trip_id = next_trip_id;
END !
DELIMITER ;