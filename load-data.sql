-- ==============================================
-- Flight Carbon Footprint Database Data Loading Script
-- ==============================================
-- This script loads data from CSV files into the database tables, 
-- performing necessary cleaning and validation steps to ensure data integrity.

-- Data for aircrafts, countries, airports, and routes are imported from 
-- OpenFlights (https://openflights.org/data.php)

-- ================================
-- LOAD DATA INTO AIRCRAFTS
-- ================================
LOAD DATA LOCAL INFILE 'data/aircrafts.csv' INTO TABLE aircrafts
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\r\n' 
IGNORE 1 ROWS; -- ignore headers

-- ================================
-- LOAD DATA INTO COUNTRIES
-- ================================
LOAD DATA LOCAL INFILE 'data/countries.csv' INTO TABLE countries
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\r\n' 
IGNORE 1 ROWS;

-- ================================
-- LOAD DATA INTO AIRPORTS
-- ================================
-- Step 1: Create a Temporary Table for Cleaning Data
CREATE TEMPORARY TABLE temp_airports (
    airport_id   CHAR(3) PRIMARY KEY,
    city         VARCHAR(100),
    country_name VARCHAR(100) NOT NULL,
    latitude     DECIMAL(18,15) NOT NULL,
    longitude    DECIMAL(18,15) NOT NULL
);

-- Step 2: Load Raw Data into temp_airports
LOAD DATA LOCAL INFILE 'data/airports.csv' 
INTO TABLE temp_airports
FIELDS TERMINATED BY ',' 
ENCLOSED BY '"' 
LINES TERMINATED BY '\r\n' 
IGNORE 1 ROWS;

-- Step 3: Remove Airports with Invalid country_name (Not in Countries Table)
DELETE FROM temp_airports
WHERE country_name NOT IN (SELECT country_name FROM countries);

-- Step 4: Insert Cleaned Data into the Actual Airports Table
INSERT INTO airports (airport_id, city, country_name, latitude, longitude)
SELECT airport_id, city, country_name, latitude, longitude FROM temp_airports;

-- Step 5: Drop the Temporary Table
DROP TEMPORARY TABLE IF EXISTS temp_airports;

-- ================================
-- LOAD DATA INTO ROUTES
-- ================================
-- Step 1: Create a Temporary Table for Cleaning Data
CREATE TEMPORARY TABLE temp_routes (
    route_id INT AUTO_INCREMENT PRIMARY KEY, -- Unique route identifier
    from_airport_id CHAR(3) NOT NULL,
    to_airport_id   CHAR(3) NOT NULL,
    aircraft_id     CHAR(3) NOT NULL
);

-- Step 2: Load Raw Data into temp_routes
LOAD DATA LOCAL INFILE 'data/routes.csv' 
INTO TABLE temp_routes
FIELDS TERMINATED BY ',' 
ENCLOSED BY '"' 
LINES TERMINATED BY '\r\n' 
IGNORE 1 ROWS;

-- Step 3: Remove Routes with Invalid References
-- Ensure aircraft_id exists in aircrafts table
DELETE FROM temp_routes
WHERE aircraft_id NOT IN (SELECT aircraft_id FROM aircrafts);

-- Ensure from_airport_id exists in airports table
DELETE FROM temp_routes WHERE from_airport_id NOT IN (
    SELECT airport_id FROM airports);

-- Ensure to_airport_id exists in airports table
DELETE FROM temp_routes WHERE to_airport_id NOT IN (
    SELECT airport_id FROM airports);

-- Step 4: Remove Duplicate Routes, Keeping Only the First Occurrence
INSERT INTO routes (from_airport_id, to_airport_id, aircraft_id)
SELECT from_airport_id, to_airport_id, aircraft_id
FROM (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY from_airport_id, to_airport_id 
    ORDER BY route_id) AS rn
    FROM temp_routes
) t
WHERE rn = 1;

-- Step 5: Drop the Temporary Table
DROP TEMPORARY TABLE IF EXISTS temp_routes;

-- ================================
-- ADD PRELOADED ADMIN USER
-- ================================
CALL sp_add_user('adminuser', 'securepass123');

-- Set the newly created user as an admin
UPDATE users SET is_admin = TRUE WHERE username = 'adminuser';

-- ================================
-- ADD PRELOADED TRIPS FOR DEMO
-- ================================

-- Trip 1: San Diego (SAN) → Denver (DEN), 1 passenger, Mid-Jan 2025
CALL sp_add_trip(1, 'SAN', 'DEN', '2025-01-15', 1);

-- Trip 2: Denver (DEN) → LAX, 1 passenger, One week after trip 1
CALL sp_add_trip(1, 'DEN', 'LAX', '2025-01-22', 1);

-- Trip 3: Denver (DEN) → Burbank (BUR), 1 passenger, First week of Jan 2025
CALL sp_add_trip(1, 'DEN', 'BUR', '2025-01-05', 1);

-- Trip 4: Burbank (BUR) → Denver (DEN), 1 passenger, Mid-Dec 2024
CALL sp_add_trip(1, 'BUR', 'DEN', '2024-12-15', 1);

-- Trip 5: Denver (DEN) → The Big Island, Hawaii (KOA), 4 passengers, Few days after trip 4
CALL sp_add_trip(1, 'DEN', 'KOA', '2024-12-18', 4);

-- Trip 6: Oahu (HNL) → Denver (DEN), 4 passengers, 10 days after trip 5
CALL sp_add_trip(1, 'HNL', 'DEN', '2024-12-28', 4);

-- Trip 7: Denver (DEN) → Ontario, CA (ONT), 1 passenger, Last week of September 2024
CALL sp_add_trip(1, 'DEN', 'ONT', '2024-09-24', 1);

-- Trip 8: LAX → Denver (DEN), 1 passenger, First week of September 2024
CALL sp_add_trip(1, 'LAX', 'DEN', '2024-09-05', 1);

-- Trip 9: LAX → Chicago (ORD), 28 passengers, Third week of October 2024
CALL sp_add_trip(1, 'LAX', 'ORD', '2024-10-21', 28);

-- Trip 10: Chicago (ORD) → LAX, 28 passengers, Four days after trip 9
CALL sp_add_trip(1, 'ORD', 'LAX', '2024-10-25', 28);