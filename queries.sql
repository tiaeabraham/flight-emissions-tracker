-- ------------Queries for Flight Carbon Footprint Tracker---------------------

-- ============================================================================
--                                app-client.py
-- ============================================================================
--  create_account()
--  1) Checks if a given username already exists in the `users` table.
--  2) Calls a stored procedure to create a new user with specified 
--     username/password.
-- ============================================================================
SELECT COUNT(*) 
FROM users 
WHERE username = 'newuser';

CALL sp_add_user('newuser', 'securepass123');

-- =========================================================================
--  login()
--  Calls a stored function to verify if the provided username and password 
--  match a valid account in the database.
-- =========================================================================
SELECT authenticate('adminuser', 'securepass123');

-- ======================================================================
--  get_user_id()
--  Retrieves the unique user_id from the `users` table for the given username.
-- ======================================================================
SELECT user_id FROM users WHERE username = 'adminuser';

-- ===========================================================
--  get_emissions()
--  1) Retrieves the distance between two airports (LAX and JFK).
--  2) Retrieves the emissions_per_mi for the aircraft operating 
--     the specified route.
--  3) Calculates total emissions for the flight given distance, 
--     emissions rate, and passenger count.
-- ===========================================================
SELECT get_trip_distance('LAX', 'JFK');

SELECT emissions_per_mi 
FROM aircrafts 
WHERE aircraft_id = (
    SELECT aircraft_id 
    FROM routes 
    WHERE from_airport_id = 'LAX' 
      AND to_airport_id = 'JFK'
);

SELECT calculate_trip_emissions('2469.45', '0.13', 2);

-- ===========================================================
--  save_trip()
--  Inserts a new trip record with the specified trip details 
--  (e.g., user_id, departure/arrival airports, date, passengers, emissions).
-- ===========================================================
INSERT INTO trips (
    user_id, 
    from_airport_id, 
    to_airport_id, 
    departure_date, 
    num_passengers, 
    total_emissions
) 
VALUES (
    '1', 
    'LAX', 
    'JFK', 
    '2008-11-21', 
    2, 
    642.057
);

-- ============================================================================
--  view_trips(user_id)
--  Gets the 10 most recent trips that the user has taken. 
-- ============================================================================
SELECT trip_id, from_airport_id, to_airport_id, departure_date, num_passengers, 
  total_emissions
FROM trips
WHERE user_id = 1
ORDER BY departure_date
LIMIT 10;

-- ============================================================================
--  insert_trip(user_id)
--  Invokes a stored procedure to calculate emissions and insert a new trip for 
--  the user.
-- ============================================================================
CALL sp_add_trip('1', 'LAX', 'DEN', '2018-11-21', 2);

-- =================================================================================
--  find_airport()
--  1) Tries to match an input against country ID or name to identify a valid country.
--  2) Based on a city name or initial letter, finds matching airports in that country.
-- =================================================================================
SELECT country_name 
FROM countries 
WHERE country_id = 'US';

SELECT country_name 
FROM countries 
WHERE country_name = 'United States';

SELECT city, airport_id 
FROM airports 
WHERE country_name = 'United States'
  AND city LIKE 'L%';

SELECT airport_id 
FROM airports 
WHERE country_name = 'United States'
  AND city = 'Denver';

-- =================================================================================
--  view_emissions_by_month(user_id)
--  Aggregates total emissions by month for a given year and displays the results.
-- =================================================================================
SELECT MONTH(departure_date) AS month, 
       SUM(total_emissions) AS total_emissions
FROM trips
WHERE user_id = '1'
  AND YEAR(departure_date) = '2025'
GROUP BY MONTH(departure_date)
ORDER BY MONTH(departure_date);


-- =================================================================================
--  view_emissions_by_year(user_id)
--  Shows total emissions by year, for up to the 10 most recent years of trips.
-- =================================================================================
SELECT YEAR(departure_date) AS year, 
       SUM(total_emissions) AS total_emissions
FROM trips
WHERE user_id = '1'
GROUP BY YEAR(departure_date)
ORDER BY YEAR(departure_date)
LIMIT 10;


-- =================================================================================
--  view_trips_by_country(user_id)
--  1) Identifies a country by ID or name.
--  2) Shows all user trips either departing from or arriving in that country, along 
--     with departure date, passenger count, and emissions.
-- =================================================================================
SELECT country_name 
FROM countries 
WHERE country_id = 'US';

-- For trips departing FROM the given country
SELECT t.from_airport_id, a1.city AS from_city, 
       t.to_airport_id, a2.city AS to_city,
       t.departure_date, t.num_passengers, t.total_emissions
FROM trips t
JOIN airports a1 ON t.from_airport_id = a1.airport_id
JOIN airports a2 ON t.to_airport_id = a2.airport_id
WHERE t.user_id = '1'
  AND a1.country_name = 'United States'
ORDER BY t.departure_date;

-- For trips arriving TO the given country
SELECT t.from_airport_id, a1.city AS from_city, 
       t.to_airport_id, a2.city AS to_city,
       t.departure_date, t.num_passengers, t.total_emissions
FROM trips t
JOIN airports a1 ON t.from_airport_id = a1.airport_id
JOIN airports a2 ON t.to_airport_id = a2.airport_id
WHERE t.user_id = '1'
  AND a2.country_name = 'United States'
ORDER BY t.departure_date;

-- =================================================================================
--  change_password(username)
--  Calls a stored procedure to update the user's password securely.
-- =================================================================================
CALL sp_change_password('adminuser', 'securepass123');

-- =================================================================================
--  delete_trip(user_id)
--  1) Fetch the maximum trip_id for this user.
--  2) Check if the trip ID exists for this user.
--  3) Delete the trip.
-- =================================================================================
SELECT MAX(trip_id) FROM trips WHERE user_id = 1;
SELECT COUNT(*) FROM trips WHERE user_id = 1 AND trip_id = 11;
DELETE FROM trips WHERE user_id = 1 AND trip_id = 11;

-- ============================================================================
--                                app-admin.py
-- ============================================================================
--  main()
--  1) Authenticates the user using the stored function `authenticate`.
--  2) Verifies if the authenticated user has admin privileges.
-- =================================================================================
SELECT authenticate('adminuser', 'securepass123');
SELECT is_admin FROM users WHERE username = 'adminuser';

-- =================================================================================
--  reset_user_password()
--  1) Checks if the specified user exists in the `users` table.
--  2) Calls a stored procedure to change that user's password.
-- =================================================================================
SELECT COUNT(*) FROM users WHERE username = 'newuser';
CALL sp_change_password('newuser', 'newpass');

-- =================================================================================
--  set_user_to_admin()
--  1) Checks if the specified user exists.
--  2) Updates that user to have admin privileges (is_admin = TRUE).
-- =================================================================================
SELECT COUNT(*) FROM users WHERE username = 'newuser';
UPDATE users SET is_admin = TRUE WHERE username = 'newuser';

-- =================================================================================
--  update_aircraft_emissions()
--  1) Checks if the specified aircraft exists.
--  2) Updates the aircraft’s emissions_per_mi value.
-- =================================================================================
SELECT COUNT(*) FROM aircrafts WHERE aircraft_id = '100';
UPDATE aircrafts SET emissions_per_mi = '0.16' WHERE aircraft_id = '100';

-- =================================================================================
--  add_new_flight_route()
--  1) Confirms that both airports exist.
--  2) Confirms the specified aircraft exists.
--  3) Ensures the route does not already exist.
--  4) Inserts a new route with the given airports and aircraft.
-- =================================================================================
SELECT COUNT(*) FROM airports WHERE airport_id = 'JFK';
SELECT COUNT(*) FROM airports WHERE airport_id = 'SIN';

SELECT COUNT(*) FROM aircrafts WHERE aircraft_id = '359';

SELECT COUNT(*) 
FROM routes 
WHERE from_airport_id = 'JFK' 
  AND to_airport_id = 'SIN';

INSERT INTO routes (from_airport_id, to_airport_id, aircraft_id) 
VALUES ('JFK', 'SIN', '359');

-- ==========================================================================