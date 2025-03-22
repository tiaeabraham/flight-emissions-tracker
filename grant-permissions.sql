-- ==============================================
-- MySQL User Permissions Setup
-- ==============================================
-- This script creates MySQL users and grants appropriate privileges
-- for application access to the Flight Carbon Footprint database.

DROP USER IF EXISTS 'appadmin'@'localhost';
DROP USER IF EXISTS 'appclient'@'localhost';

-- ================================
-- CREATE USERS
-- ================================
-- Admin user: Has full privileges over non-user-specific tables
CREATE USER 'appadmin'@'localhost' IDENTIFIED BY 'adminpw';

-- Client user: Can read data and manage their own trips/login info
CREATE USER 'appclient'@'localhost' IDENTIFIED BY 'clientpw';

-- ================================
-- GRANT PERMISSIONS
-- ================================
-- Admin user gets full privileges on tables they manage
GRANT SELECT, INSERT ON tripsdb.routes TO 'appadmin'@'localhost';
GRANT SELECT, UPDATE ON tripsdb.users TO 'appadmin'@'localhost';
GRANT SELECT ON tripsdb.airports TO 'appadmin'@'localhost';
GRANT SELECT, UPDATE ON tripsdb.aircrafts TO 'appadmin'@'localhost';
GRANT EXECUTE ON FUNCTION tripsdb.authenticate TO 'appadmin'@'localhost';
GRANT EXECUTE ON PROCEDURE tripsdb.sp_change_password TO 'appadmin'@'localhost';

-- Client user can read all data but manage only their own trips & login info
GRANT SELECT ON tripsdb.* TO 'appclient'@'localhost';
GRANT INSERT, DELETE ON tripsdb.trips TO 'appclient'@'localhost';
GRANT INSERT, UPDATE, DELETE ON tripsdb.users 
    TO 'appclient'@'localhost';
GRANT EXECUTE ON PROCEDURE tripsdb.sp_add_trip TO 'appclient'@'localhost';
GRANT EXECUTE ON PROCEDURE tripsdb.sp_add_user TO 'appclient'@'localhost';
GRANT EXECUTE ON PROCEDURE tripsdb.sp_add_trip TO 'appclient'@'localhost';
GRANT EXECUTE ON PROCEDURE tripsdb.sp_change_password TO 'appclient'@'localhost';
GRANT EXECUTE ON FUNCTION tripsdb.authenticate TO 'appclient'@'localhost';
GRANT EXECUTE ON FUNCTION tripsdb.get_trip_distance TO 'appclient'@'localhost';
GRANT EXECUTE ON FUNCTION tripsdb.calculate_trip_emissions TO 'appclient'@'localhost';