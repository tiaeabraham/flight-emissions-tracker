import sys  # To print error messages to sys.stderr
import mysql.connector
import pandas as pd
from tabulate import tabulate
from datetime import datetime

def get_conn():
    """
    Establishes a connection to the MySQL database.
    Returns:
        conn (mysql.connector.connection): The database connection object.
    If unsuccessful, exits with an error message.
    """
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='appclient',  # Client user with restricted access
            port='3306',  # Default MySQL port
            password='clientpw',
            database='tripsdb'
        )
        return conn
    except mysql.connector.Error:
        sys.stderr.write('Database access attempt failed, please contact the system administrator.\n')
        sys.exit(1)

def show_options(type, username=None):
    """
    Displays options for user authentication.
    """
    if type == "login":
        print('\n------------------Flight Carbon Footprint Tracker------------------')
        print('1. Log In')
        print('2. Create an Account')
        print('3. Exit')
    elif type == "main":
        print(f"\n-----------------------Welcome {username}!------------------------")
        print("1. Get Emissions Estimate")
        print("2. View Saved Trips")
        print("3. Insert a New Trip")
        print("4. Delete a Trip")
        print("5. Find an Airport")
        print("6. Change Password")
        print("7. Log Out")
    elif type == "save":
        print("\n-----------------Would you like to save this trip?-----------------")
        print("1. Save Trip")
        print("2. Go Back to Main Menu")
    elif type == "view":
        print("\n-------------------View Trip Aggregate Emissions-------------------")
        print("1. View Trip Emissions by Year")
        print("2. View Trip Emissions by Month")
        print("3. View Trips to/from a Country")
        print("4. Go Back to Main Menu")

def create_account():
    """
    Handles user account creation by calling stored procedure `sp_add_user`.
    """
    conn = get_conn()
    cursor = conn.cursor()
    print('\n--------Welcome! Please provide login information below.-----------')

    username = input('Enter a username: ').strip().lower()
    if len(username) < 3:
        print("Error: Username must be at least 3 characters. Please try again.")
        return
    elif len(username) > 20:
        print("Error: Username must be at most 20 characters. Please try again.")
        return
    
    # Check if username already exists
    try:
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = %s;", (username,))
        result = cursor.fetchone()
        if result and result[0] > 0:
            print("Error: This username already exists. Please choose a different one.")
            return
    except mysql.connector.Error:
        print("Database access attempt failed. Please contact the system administrator.")
        cursor.close()
        conn.close()
        return  # Exit the function since we can't verify username existence

    while True:
        password = input('Enter a password: ').strip()
        if len(password) < 3:
            print("Error: Password must be at least 3 characters. Please try again.")
        elif len(password) > 20:
            print("Error: Password must be at most 20 characters. Please try again.")
        else:
            break

    # Attempt to create the account
    try:
        cursor.callproc('sp_add_user', (username.lower(), password))
        conn.commit()
        print('Account created successfully! Please log in.')
    except mysql.connector.Error:
        print("Database update failed. Please contact the system administrator.")
    finally:
        cursor.close()
        conn.close()

def login():
    """
    Handles user login by calling stored function `authenticate`.
    """
    conn = get_conn()
    cursor = conn.cursor()
    print('\n-----------Please enter your login credentials below.---------------')
    username = input('Enter your username: ').strip().lower()
    if len(username) < 3:
        print("Error: Username must be at least 3 characters. Please try again.")
        return
    elif len(username) > 20:
        print("Error: Username must be at most 20 characters. Please try again.")
        return
    password = input('Enter your password: ').strip()
    if len(password) < 3:
        print("Error: Password must be at least 3 characters. Please try again.")
        return
    elif len(password) > 20:
        print("Error: Password must be at most 20 characters. Please try again.")
        return
    
    try:
        cursor.execute("SELECT authenticate(%s, %s);", (username.lower(), password))
        result = cursor.fetchone()
        if result[0] == 1:
            print('Login successful!')
            return username.lower()
        else:
            print('Invalid credentials. Please try again.')
            return
    except mysql.connector.Error as err:
        print("Database access attempt failed. Please contact the system administrator.")
        return
    finally:
        cursor.close()
        conn.close()

def get_user_id(username):
    """
    Retrieves the user_id for a given username.
    """
    conn = get_conn()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT user_id FROM users WHERE username = %s;", (username,))
        result = cursor.fetchone()
        if result:
            return result[0]  # Return the user_id
        else:
            print("Error: User not found.")
            return
    except mysql.connector.Error:
        print("Database access attempt failed. Please contact the system administrator.")
        return
    finally:
        cursor.close()
        conn.close()

def get_emissions(user_id):
    """
    Calculates and displays estimated emissions for a flight.
    """
    from_airport_id = input("Enter departure airport ID (i.e., LAX): ").upper().strip()
    to_airport_id = input("Enter destination airport ID (i.e., JFK): ").upper().strip()
    if len(from_airport_id) != 3 or len(to_airport_id) != 3:
        print("Error: Airport ID must be 3 characters. Please try again.")
        return
    
    num_passengers = int(input("Enter the number of passengers: ").strip())
    if num_passengers < 0:
        print("Error: Number of passengers must be a non-negative value.")
        return
    elif num_passengers == 0:
        print("Error: Number of passengers must be a non-zero value.")
        return
    elif num_passengers > 853:
        print("Error: Number of passengers is too large. The largest place can only hold 853 passengers!")
        return

    conn = get_conn()
    cursor = conn.cursor()

    try:
        # Get trip distance
        cursor.execute("SELECT get_trip_distance(%s, %s);", (from_airport_id, to_airport_id))
        distance = cursor.fetchone()[0]

        if distance is None:
            print("\nError: No flight route found between these airports.")
            print("If you would like to update the database with this flight route,")
            print("please contact your system administrator.")
            return

        # Get emissions per mile from routes
        cursor.execute("SELECT emissions_per_mi FROM aircrafts WHERE aircraft_id = ("
                       "SELECT aircraft_id FROM routes WHERE from_airport_id = %s AND to_airport_id = %s);",
                       (from_airport_id, to_airport_id))
        emissions_per_mi = cursor.fetchone()

        if emissions_per_mi is None:
            print("Error: No emission data available for this route.")
            return

        emissions_per_mi = emissions_per_mi[0]

        # Calculate total emissions
        cursor.execute("SELECT calculate_trip_emissions(%s, %s, %s);", 
                       (distance, emissions_per_mi, num_passengers))
        total_emissions = cursor.fetchone()[0]

        print(f"\nEstimated emissions for flight from {from_airport_id} to {to_airport_id}: {total_emissions:.2f} kg CO₂\n")

        # Prompt the user to save the trip
        save_trip(user_id, from_airport_id, to_airport_id, num_passengers, total_emissions)

    except mysql.connector.Error:
        print("Database access attempt failed. Please contact the system administrator.")

    finally:
        cursor.close()
        conn.close()

def get_valid_date():
    """
    Asks the user for a valid departure date in YYYY-MM-DD format.
    Ensures the input is properly formatted and represents a real date.
    """
    date_input = input("Enter departure date (YYYY-MM-DD): ").strip()

    try:
        # Convert to a datetime object to validate the format and existence
        departure_date = datetime.strptime(date_input, "%Y-%m-%d").date()

        return departure_date  # Return valid date

    except ValueError:
        print("Error: Invalid date format. Please enter the date in YYYY-MM-DD format.")
        return

def save_trip(user_id, from_airport_id, to_airport_id, num_passengers, total_emissions):
    """
    Allows the user to save a trip to the database.
    Calls the stored procedure `sp_add_trip` to store trip details.
    """
    while True:
        show_options("save")
        choice = input("Select an option: ").strip()

        if choice == '1':  # Save the trip
            departure_date = get_valid_date()
            if not departure_date:
                save_trip(user_id, from_airport_id, to_airport_id, num_passengers, total_emissions)
                return

            conn = get_conn()
            cursor = conn.cursor()

            try:
                cursor.execute(
                    'INSERT INTO trips (user_id, from_airport_id, to_airport_id, departure_date, num_passengers, total_emissions) VALUES (%s, %s, %s, %s, %s, %s);', (user_id, from_airport_id, to_airport_id, departure_date, num_passengers, total_emissions))
                conn.commit()
                print("Trip successfully saved!")

            except mysql.connector.Error as err:
                print("Database update failed. Please contact the system administrator.")
                print(f'Error: {err}')

            finally:
                cursor.close()
                conn.close()
            
            break  # Exit save menu after saving

        elif choice == '2':  # Go back to the main menu
            print("Returning to main menu...")
            break

        else:
            print("Invalid option. Please try again.")

def view_trips(user_id):
    """
    Fetches and displays the user's last 10 trips in a formatted table.
    Also calculates the total emissions from all recorded trips.
    """
    conn = get_conn()
    cursor = conn.cursor()

    try:
        # Query trips directly
        cursor.execute("""
            SELECT trip_id, from_airport_id, to_airport_id, departure_date,
                   num_passengers, total_emissions
            FROM trips
            WHERE user_id = %s
            ORDER BY departure_date
            LIMIT 10;
        """, (user_id,))
        
        results = cursor.fetchall()

        if not results:
            print("No saved trips found.")
            return

        # Convert results to DataFrame
        df = pd.DataFrame(results, columns=["Trip ID", "From", "To", "Departure Date", "Passengers", "Emissions (kg CO₂)"])
        df["Departure Date"] = pd.to_datetime(df["Departure Date"]).dt.strftime("%m-%d-%Y")
        df["Passengers"] = df["Passengers"].astype(int)
        df["Emissions (kg CO₂)"] = df["Emissions (kg CO₂)"].astype(float)

        # Calculate total emissions across the 10 most recent trips
        total_emissions = df["Emissions (kg CO₂)"].sum()

        # Display the table
        print("\nYour Last 10 Trips:\n")
        print(tabulate(df, headers="keys", tablefmt="grid", showindex=False))
        print(f"\nTotal CO₂ Emissions from These Trips: {total_emissions:.2f} kg\n")

        while True:
            show_options("view")
            view_choice = input("Select an option: ").strip()

            if view_choice == '1':
                view_emissions_by_year(user_id)
            elif view_choice == '2':
                view_emissions_by_month(user_id)
            elif view_choice == '3':
                view_trips_by_country(user_id)
            elif view_choice == '4':
                break
            else:
                print("Invalid option. Please try again.")

    except mysql.connector.Error:
        print("Database access attempt failed. Please contact the system administrator.")

    finally:
        cursor.close()
        conn.close()

def insert_trip(user_id):
    """
    Inserts a new trip by taking in airport IDs, departure date, and passengers.
    Calls `sp_add_trip()`, which calculates emissions and inserts the trip.
    """
    from_airport_id = input("Enter departure airport ID (i.e., LAX): ").upper().strip()
    to_airport_id = input("Enter destination airport ID (i.e., JFK): ").upper().strip()
    if len(from_airport_id) != 3 or len(to_airport_id) != 3:
        print("Error: Airport ID must be 3 characters. Please try again.")
        return
        
    departure_date = get_valid_date()
    if not departure_date:
        return

    num_passengers = int(input("Enter the number of passengers: ").strip())
    if num_passengers < 0:
        print("Error: Number of passengers must be a non-negative value.")
        return
    elif num_passengers == 0:
        print("Error: Number of passengers must be a non-zero value.")
        return
    elif num_passengers > 853:
        print("Error: Number of passengers is too large. The largest place can only hold 853 passengers!")
        return

    conn = get_conn()
    cursor = conn.cursor()

    try:
        # Check if route exists
        cursor.execute("SELECT get_trip_distance(%s, %s);", (from_airport_id, to_airport_id))
        distance = cursor.fetchone()[0]

        if distance is None:
            print("\nError: No flight route found between these airports.")
            print("If you would like to update the database with this flight route,")
            print("please contact your system administrator.")
            return

        # Add trip
        cursor.callproc('sp_add_trip', (user_id, from_airport_id, to_airport_id, 
                                        departure_date, num_passengers))
        conn.commit()
        print("Trip successfully inserted!")

    except mysql.connector.Error:
        print("Database update failed. Please contact the system administrator.")

    finally:
        cursor.close()
        conn.close()

def find_airport():
    """
    Finds airports based on a given country ID or country name and an optional 
    city name or first letter.
    """
    conn = get_conn()
    cursor = conn.cursor()

    try:
        # Step 1: Get Country Name or ID
        country_input = input("Enter a country name or country ID (ISO 2-letter \
code): ").strip()

        if len(country_input) == 2:  # Assume ISO country code is given
            cursor.execute("SELECT country_name FROM countries WHERE \
                           country_id = %s;", (country_input.upper(),))
            result = cursor.fetchone()
            if result:
                country_name = result[0]
            else:
                print("Error: No airports found for the given country ID.")
                return
        else:  # Assume full country name is given
            cursor.execute("SELECT country_name FROM countries WHERE "
            "country_name = %s;", (country_input.title(),))
            result = cursor.fetchone()
            if result:
                country_name = result[0]
            else:
                print("Error: No airports found for the given country name.")
                return

        # Step 2: Get City Name or First Letter
        print("Enter a city name or first letter of the city")
        city_input = input(f"(Enter blank for all airports in {country_name}): ").strip()

        if len(city_input) == 1:  # User entered only one letter
            cursor.execute(
                "SELECT city, airport_id FROM airports WHERE country_name = %s"
                " AND city LIKE %s ORDER BY city;",
                (country_name, city_input.upper() + '%')
            )
            results = cursor.fetchall()
            if results:
                print(f"\nMatching Airports in {country_name} in Cities \
Starting with `{city_input.upper()}`")
                print("+---------------------------+------------+")
                print("| City                      | Airport ID |")
                print("+---------------------------+------------+")
                for city, airport_id in results:
                    print(f"| {city:<25} | {airport_id:<10} |")
                print("+---------------------------+------------+")
            else:
                print("Error: No cities found in the given country with that \
first letter.")

        elif len(city_input) >= 3:  # User entered a full city name
            city_input = city_input.title()
            cursor.execute(
                "SELECT airport_id FROM airports WHERE country_name = %s AND \
                    city = %s ORDER BY city;",
                (country_name, city_input)
            )
            results = cursor.fetchall()
            if results:
                print(f"\nMatching Airports in {city_input}, {country_name}")
                print("+------------+")
                print("| Airport ID |")
                print("+------------+")
                for airport_id in results:
                    print(f"| {airport_id[0]:<10} |")
                print("+------------+")
            else:
                print("Error: No airport found for the given city.")
        else: # display all the airports in the given country
            cursor.execute(
                "SELECT city, airport_id FROM airports WHERE \
                    country_name = %s ORDER BY city;",
                (country_name,)
            )
            results = cursor.fetchall()
            if results:
                print("\nMatching Airports in", country_name)
                print("+---------------------------+------------+")
                print("| City                      | Airport ID |")
                print("+---------------------------+------------+")
                for city, airport_id in results:
                    print(f"| {city:<25} | {airport_id:<10} |")
                print("+---------------------------+------------+")
            else:
                print("Error: No airports found for the given country.")

    except mysql.connector.Error:
        print("Database access attempt failed. Please contact the system \
administrator.")

    finally:
        cursor.close()
        conn.close()

def view_emissions_by_month(user_id):
    """
    Displays the total trip emissions per month for a given year.
    Uses GROUP BY, SUM, COUNT, and JOINs.
    """
    year = input("Enter the year to view emissions (i.e., 2024): ").strip()

    conn = get_conn()
    cursor = conn.cursor()

    try:
        # Query for emissions per month
        query = """
        SELECT MONTH(departure_date) AS month, 
               SUM(total_emissions) AS total_emissions
        FROM trips
        WHERE user_id = %s AND YEAR(departure_date) = %s
        GROUP BY MONTH(departure_date)
        ORDER BY MONTH(departure_date);
        """
        cursor.execute(query, (user_id, year))
        emissions_results = cursor.fetchall()

        if not emissions_results:
            print(f"No trips found for the year {year}.")
            return

        # Convert to DataFrames
        df = pd.DataFrame(emissions_results, columns=["Month", "Total Emissions (kg CO₂)"])

        # Convert month numbers to names
        df["Month"] = df["Month"].astype(int).apply(lambda x: pd.to_datetime(f"{x}", format="%m").strftime("%B"))
        
        # Calculate total emissions
        total_emissions = df["Total Emissions (kg CO₂)"].sum()

        # Print table
        print(f"\nTrip Emissions by Month for {year}:\n")
        print(tabulate(df, headers="keys", tablefmt="grid", showindex=False))

        print(f"\nTotal Emissions for {year}: {total_emissions:.2f} kg CO₂\n")

    except mysql.connector.Error:
        print("Database access attempt failed. Please contact the system administrator.")

    finally:
        cursor.close()
        conn.close()

def view_emissions_by_year(user_id):
    """
    Displays total trip emissions per year for the 10 most recent years.
    Uses GROUP BY, SUM, COUNT, and JOINs.
    """
    conn = get_conn()
    cursor = conn.cursor()

    try:
        # Query for emissions per year (last 10 years)
        query = """
        SELECT YEAR(departure_date) AS year, 
               SUM(total_emissions) AS total_emissions
        FROM trips
        WHERE user_id = %s
        GROUP BY YEAR(departure_date)
        ORDER BY YEAR(departure_date)
        LIMIT 10;
        """
        cursor.execute(query, (user_id,))
        emissions_results = cursor.fetchall()

        if not emissions_results:
            print("No trips found.")
            return

        # Convert to DataFrames
        df = pd.DataFrame(emissions_results, columns=["Year", "Total Emissions (kg CO₂)"])

        # Calculate total emissions
        total_emissions = df["Total Emissions (kg CO₂)"].sum()

        # Print table
        print("\nTrip Emissions by Year (10 Most Recent Years):\n")
        print(tabulate(df, headers="keys", tablefmt="grid", showindex=False))

        print(f"\nTotal Emissions from Your 10 Most Recent Years: {total_emissions:.2f} kg CO₂\n")

    except mysql.connector.Error:
        print("Database access attempt failed. Please contact the system administrator.")

    finally:
        cursor.close()
        conn.close()

def view_trips_by_country(user_id):
    """
    Displays all trips either departing from or arriving in a given country.
    Uses JOINs between trips, airports, and countries to fetch country-based trips.
    """
    conn = get_conn()
    cursor = conn.cursor()

    try:
        # Step 1: Get Country Name or ID
        country_input = input("Enter a country name or country ID (ISO 2-letter code): ").strip()

        if len(country_input) == 2:  # Assume country ID is given
            cursor.execute("SELECT country_name FROM countries WHERE country_id = %s;", (country_input,))
            result = cursor.fetchone()
            if result:
                country_name = result[0]
            else:
                print("Error: No trips found for the given country ID.")
                return
        else:  # Assume full country name is given
            cursor.execute("SELECT country_name FROM countries WHERE country_name = %s;", (country_input,))
            result = cursor.fetchone()
            if result:
                country_name = result[0]
            else:
                print("Error: No trips found for the given country name.")
                return

        # Step 2: Ask if the user wants "From" or "To"
        direction = input("Do you want to see trips departing FROM or arriving TO this country? (Enter 'from' or 'to'): ").strip().lower()
        while direction.strip().lower() not in ["from", "to"]:
            print("Invalid input. Please enter 'from' or 'to'.")
            direction = input("Do you want to see trips departing FROM or arriving TO this country? (Enter 'from' or 'to'): ").strip().lower()

        # Step 3: Choose the appropriate query
        if direction == "from":
            query = """
            SELECT t.trip_id, t.from_airport_id, a1.city AS from_city, t.to_airport_id, a2.city AS to_city,
                   t.departure_date, t.num_passengers, t.total_emissions
            FROM trips t
            JOIN airports a1 ON t.from_airport_id = a1.airport_id
            JOIN airports a2 ON t.to_airport_id = a2.airport_id
            WHERE t.user_id = %s AND a1.country_name = %s
            ORDER BY t.departure_date
            LIMIT 10;
            """
        else:  # direction == "to"
            query = """
            SELECT t.trip_id, t.from_airport_id, a1.city AS from_city, t.to_airport_id, a2.city AS to_city,
                   t.departure_date, t.num_passengers, t.total_emissions
            FROM trips t
            JOIN airports a1 ON t.from_airport_id = a1.airport_id
            JOIN airports a2 ON t.to_airport_id = a2.airport_id
            WHERE t.user_id = %s AND a2.country_name = %s
            ORDER BY t.departure_date
            LIMIT 10;
            """

        cursor.execute(query, (user_id, country_name))
        results = cursor.fetchall()

        if not results:
            print(f"No trips found {direction} {country_name}.")
            return

        # Convert to DataFrame
        df = pd.DataFrame(results, columns=["Trip ID", "From Airport", "From City", "To Airport", "To City", "Departure Date", "Passengers", "Emissions (kg CO₂)"])

        # Format date
        df["Departure Date"] = pd.to_datetime(df["Departure Date"]).dt.strftime("%m-%d-%Y")

        # Calculate total emissions
        total_emissions = df["Emissions (kg CO₂)"].sum()

        # Print table
        print(f"\n10 Most Recent Trips {direction} {country_name}:\n")
        print(tabulate(df, headers="keys", tablefmt="grid", showindex=False))

        print(f"\nTotal Emissions from Trips {direction} {country_name}: {total_emissions:.2f} kg CO₂\n")

    except mysql.connector.Error:
        print("Database access attempt failed. Please contact the system administrator.")

    finally:
        cursor.close()
        conn.close()

def change_password(username):
    """
    Allows the user to change their password using `sp_change_password`.
    """
    conn = get_conn()
    cursor = conn.cursor()

    new_password = input('Enter your new password: ')
    if len(new_password) < 3:
        print("Error: Password should be at least 3 characters. Please try again.")
        return

    try:
        cursor.callproc('sp_change_password', (username, new_passw