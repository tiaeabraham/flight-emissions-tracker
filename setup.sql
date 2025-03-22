-- ==============================================
-- Flight Carbon Footprint Database Schema
-- ==============================================
-- This script sets up the database for tracking carbon emissions from air 
-- travel. The database is designed to store user data, flight distances, 
-- aircraft emissions, and trip details. The schema ensures data integrity 
-- with foreign key constraints and optimized queries with indexes.

-- ================================
-- DROP TABLES (to reset the schema)
-- ================================
DROP TABLE IF EXISTS trips;
DROP VIEW IF EXISTS distance_view; -- Precomputed distances using lat/long
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS routes;
DROP TABLE IF EXISTS airports;
DROP TABLE IF EXISTS countries;
DROP TABLE IF EXISTS aircrafts;

-- ================================
-- CREATE TABLE: users
-- Stores user login credentials and basic information.
-- Also stores a user's password with a hash and fixed salt value.
-- ================================
CREATE TABLE users (
    user_id       INT AUTO_INCREMENT PRIMARY KEY ,
    username      VARCHAR(20)        UNIQUE NOT NULL,
    salt          CHAR(8)            NOT NULL,
    password_hash BINARY(64)         NOT NULL, -- Hashed password for security
    is_admin      BOOLEAN            DEFAULT FALSE
);

-- ================================
-- CREATE TABLE: countries
-- Stores country codes and names to standardize location data.
-- ================================
CREATE TABLE countries (
     -- Full country name (i.e. United States)
    country_name VARCHAR(100) PRIMARY KEY,   
    -- ISO Alpha-2 country code (i.e., US, CA, AU)
    country_id   CHAR(2)      NOT NULL
);

-- ================================
-- CREATE TABLE: airports
-- Stores airport information, including location details.
-- ================================
CREATE TABLE airports (
    -- IATA code for airport (i.e., LAX, JFK)
    airport_id   CHAR(3)        PRIMARY KEY, 
    -- Some airports may not have associated city names
    city         VARCHAR(100)   DEFAULT NULL,
    -- References a country in the countries table
    country_name VARCHAR(100)   NOT NULL,
    -- Geographic latitude and longitude of airport
    latitude     DECIMAL(18,15) NOT NULL,
    longitude    DECIMAL(18,15) NOT NULL,
    FOREIGN KEY (country_name) REFERENCES countries(country_name)
        ON DELETE CASCADE
);

-- ================================
-- CREATE TABLE: aircrafts
-- Stores aircraft models and their carbon emissions per mile per passenger.
-- ================================
CREATE TABLE aircrafts (
    -- IATA code for aircraft (i.e., 787, 78J)
    aircraft_id      CHAR(3)      PRIMARY KEY,
    -- Aircraft model name (i.e., Boeing 747, Airbus A320)
    model            VARCHAR(100) NOT NULL,
    -- Average CO2 emissions in kg per mile per passenger
    emissions_per_mi FLOAT        NOT NULL
);

-- ================================
-- CREATE TABLE: routes
-- Stores predefined flight routes and associated aircrafts.
-- ================================
CREATE TABLE routes (
    from_airport_id CHAR(3) NOT NULL, -- Departure airport
    to_airport_id   CHAR(3) NOT NULL, -- Arrival airport
    aircraft_id     CHAR(3) NOT NULL, -- Aircraft assigned to the route
    PRIMARY KEY (from_airport_id, to_airport_id),
    FOREIGN KEY (from_airport_id) REFERENCES airports(airport_id) 
         ON DELETE CASCADE,
    FOREIGN KEY (to_airport_id) REFERENCES airports(airport_id) 
        ON DELETE CASCADE,
    FOREIGN KEY (aircraft_id) REFERENCES aircrafts(aircraft_id) 
        ON DELETE CASCADE
);

-- ================================
-- CREATE VIEW: distance_view
-- Precomputes flight distances between airport pairs using the Haversine 
-- formula.
-- ================================
CREATE VIEW distance_view AS
SELECT 
    r.from_airport_id,
    r.to_airport_id,
    r.aircraft_id,
    COALESCE(
        (6371 * acos(
            cos(radians(a1.latitude)) * cos(radians(a2.latitude)) * 
            cos(radians(a2.longitude) - radians(a1.longitude)) +
            sin(radians(a1.latitude)) * sin(radians(a2.latitude))
        ) * 0.621371),  -- Convert km to miles
        NULL  -- If computation fails, return NULL instead of dropping the row
    ) AS distance_mi
FROM routes r
LEFT JOIN airports a1 ON r.from_airport_id = a1.airport_id
LEFT JOIN airports a2 ON r.to_airport_id = a2.airport_id;

-- ================================
-- CREATE TABLE: trips
-- Stores user trip details and their total carbon footprint calculations.
-- ================================
CREATE TABLE trips (
    trip_id         BIGINT             NOT NULL, -- User-specific trip ID
    user_id         INT                NOT NULL, -- Links trip to a user
    from_airport_id CHAR(3)            NOT NULL, -- Departure airport
    to_airport_id   CHAR(3)            NOT NULL, -- Arrival airport
    departure_date  DATE               NOT NULL, -- Date of departure
    num_passengers  INT     NOT NULL CHECK (num_passengers > 0),
    total_emissions FLOAT              NOT NULL,
    PRIMARY KEY (user_id, trip_id),  -- PK is now user_id + trip_id
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (from_airport_id, to_airport_id) REFERENCES 
        routes(from_airport_id, to_airport_id) ON DELETE CASCADE
);

-- ================================
-- Composite index to speed up searches by country and first letter of city 
-- name.
-- ================================
CREATE INDEX idx_airports_country_city ON airports (country_name, city(1));