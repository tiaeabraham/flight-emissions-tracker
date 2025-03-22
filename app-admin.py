import mysql.connector
import sys  # To print error messages to sys.stderr

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
            user='appadmin',  # Admin user 
            port='3306',  # Default MySQL port
            password='adminpw',
            database='tripsdb'
        )
        return conn
    except mysql.connector.Error:
        sys.stderr.write('Database access attempt failed, please contact the system administrator.\n')
        sys.exit(1)

def show_options():
    """
    Displays the admin main menu.
    """
    print("\n------------------Admin Dashboard------------------")
    print("1. Reset a User's Password")
    print("2. Set a User to Admin")
    print("3. Update Aircraft Emissions")
    print("4. Add a New Flight Route")
    print("5. Exit")

def reset_user_password():
    """
    Allows an admin to reset a user's password.
    Ensures the user exists and the new password is at least 3 characters.
    """
    conn = get_conn()
    cursor = conn.cursor()

    username = input("Enter the username to reset the password for: ").strip().lower()

    if len(username) < 3:
        print("Error: Username should be at least 3 characters. Please try again.")
        return

    # Check if username exists
    try:
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = %s;", (username,))
        result = cursor.fetchone()
        if result and result[0] == 0:
            print("Error: This username does not exist. Please input a valid username.")
            return
    except mysql.connector.Error:
        print("Database access attempt failed. Please contact the system administrator.")
        cursor.close()
        conn.close()
        return  # Exit the function since we can't verify username existence
    
    # Get new password
    new_password = input("Enter the new password (at least 3 characters): ").strip()
    if len(new_password) < 3:
        print("Error: Password must be at least 3 characters. Returning to the main menu.")
        return
    elif len(new_password) > 20:
        print("Error: Password must be at most 20 characters. Returning to the main menu.")
        return

    try:
        # Call stored procedure to reset password
        cursor.callproc('sp_change_password', (username, new_password))
        conn.commit()
        print("Password successfully reset!")

    except mysql.connector.Error:
        print("Database update failed. Please contact the system administrator.")

    finally:
        cursor.close()
        conn.close()

def set_user_to_admin():
    """
    Allows an admin to set another user as an admin.
    Ensures the user exists before updating.
    """
    conn = get_conn()
    cursor = conn.cursor()

    username = input("Enter the username to set as an admin: ").strip().lower()

    if len(username) < 3:
        print("Error: Username should be at least 3 characters. Please try again.")
        return

    # Check if username exists
    try:
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = %s;", (username,))
        result = cursor.fetchone()
        if result and result[0] == 0:
            print("Error: This username does not exist. Please input a valid username.")
            return
    except mysql.connector.Error as err:
        print("Database access attempt failed. Please contact the system administrator.")
        cursor.close()
        conn.close()
        return  # Exit the function since we can't verify username existence

    try:
        # Check if the user is already an admin
        cursor.execute("SELECT is_admin FROM users WHERE username = %s;", (username,))
        is_admin = cursor.fetchone()
        if is_admin and is_admin[0] == 1:
            print("Error: Username is already an admin. Returning to main menu.")
            return

        # Update is_admin flag
        cursor.execute("UPDATE users SET is_admin = TRUE WHERE username = %s;", (username,))
        conn.commit()
        print(f"User '{username}' is now an admin.")

    except mysql.connector.Error as err:
        print("Database update failed. Please contact the system administrator.")

    finally:
        cursor.close()
        conn.close()

def update_aircraft_emissions():
    """
    Allows an admin to update an aircraft's emissions per mile.
    Ensures the aircraft exists and the new value is between 0 and 1.
    """
    conn = get_conn()
    cursor = conn.cursor()

    # Get aircraft ID
    aircraft_id = input("Enter the aircraft ID to update emissions for: ").upper().strip()

    if len(aircraft_id) != 3:
        print("Error: Aircraft IATA code should be 3 characters. Please try again.")
        return

    # Check if aircraft exists
    try:
        cursor.execute("SELECT COUNT(*) FROM aircrafts WHERE aircraft_id = %s;", (aircraft_id,))
        result = cursor.fetchone()
        if result and result[0] == 0:
            print("Error: Aircraft ID not found. Returning to the main menu.")
            return
    except mysql.connector.Error:
        print("Database access attempt failed. Please contact the system administrator.")
        cursor.close()
        conn.close()
        return  # Exit the function since we can't verify aircraft existence    

    # Get new emissions value
    while True:
        try:
            new_emissions = float(input("Enter the new emissions value (0.0 - 1.0): ").strip())
            if new_emissions <= 0 or new_emissions > 1:
                print("Error: Emissions value must be greater than 0 and less than or equal to 1.")
            else:
                new_emissions = round(new_emissions, 2)
                break
        except ValueError:
            print("Error: Please enter a valid numerical value.")

    try:
        # Update emissions value
        cursor.execute("UPDATE aircrafts SET emissions_per_mi = %s WHERE aircraft_id = %s;", (new_emissions, aircraft_id))
        conn.commit()
        print(f"Updated emissions for aircraft {aircraft_id} to {new_emissions} kg CO₂ per mile.")

    except mysql.connector.Error:
        print("Database update failed. Please contact the system administrator.")

    finally:
        cursor.close()
        conn.close()

def add_new_flight_route():
    """
    Allows an admin to add a new flight route.
    Ensures the airports and aircraft exist and that the route does not already exist.
    """
    conn = get_conn()
    cursor = conn.cursor()

    # Get valid airport IDs
    from_airport_id = input("Enter departure airport ID (i.e., LAX): ").upper().strip()
    to_airport_id = input("Enter destination airport ID (i.e., JFK): ").upper().strip()
    if len(from_airport_id) != 3 or len(to_airport_id) != 3:
        print("Error: Airport ID must be 3 characters. Please try again.")
        return
    
    try:
        # Check if airports exist
        cursor.execute("SELECT COUNT(*) FROM airports WHERE airport_id = %s;", (from_airport_id,))
        from_exists = cursor.fetchone()[0]
        if from_exists == 0:
            print("Error: The source inputted airport does not exist. Returning to main menu.")
            return
        cursor.execute("SELECT COUNT(*) FROM airports WHERE airport_id = %s;", (to_airport_id,))
        to_exists = cursor.fetchone()[0]
        if to_exists == 0:
            print("Error: The destination inputted airport does not exist. Returning to main menu.")
            return

        # Get valid aircraft ID
        aircraft_id = input("Enter aircraft ID: ").upper().strip()
        cursor.execute("SELECT COUNT(*) FROM aircrafts WHERE aircraft_id = %s;", (aircraft_id,))
        aircraft_exists = cursor.fetchone()[0]

        if aircraft_exists == 0:
            print("Error: Aircraft ID does not exist. Returning to main menu.")
            return

        # Check if the route already exists
        cursor.execute("SELECT COUNT(*) FROM routes WHERE from_airport_id = %s AND to_airport_id = %s;", 
                    (from_airport_id, to_airport_id))
        route_exists = cursor.fetchone()[0]

        if route_exists > 0:
            print("Error: This route already exists. Returning to main menu.")
            return

        # Insert new flight route
        cursor.execute("INSERT INTO routes (from_airport_id, to_airport_id, aircraft_id) VALUES (%s, %s, %s);",
                       (from_airport_id, to_airport_id, aircraft_id))
        conn.commit()
        print(f"New route added: {from_airport_id} → {to_airport_id} using aircraft {aircraft_id}.")

    except mysql.connector.Error:
        print("Database update failed. Please contact the system administrator.")

    finally:
        cursor.close()
        conn.close()

def login():
    """
    Handles admin login by calling stored function `authenticate`.
    Checks if the admin's login information is valid, and if the user has
    admin permissions.
    """
    print("\n------------------- Admin Login ------------------")
    username = input("Enter admin username: ").strip().lower()  # Normalize username
    password = input("Enter admin password: ")

    # Establish database connection
    conn = get_conn()
    cursor = conn.cursor()

    try:
        # Step 1: Authenticate username and password
        cursor.execute("SELECT authenticate(%s, %s);", (username, password))
        result = cursor.fetchone()

        if result[0] == 0:
            print("Error: Invalid credentials. Exiting.")
            return False

        # Step 2: Check if the user is an admin
        cursor.execute("SELECT is_admin FROM users WHERE username = %s;", (username,))
        is_admin = cursor.fetchone()

        if not is_admin or is_admin[0] == 0:
            print("Error: User does not have admin privileges. Exiting.")
            return False

        print("Admin login successful.")

    except mysql.connector.Error:
        print("Database access attempt failed. Please contact the system administrator.")
        return False

    finally:
        cursor.close()
        conn.close()
    return True

def main():
    """
    Main program loop for admin functionalities.
    """
    if not login():
        return

    # Admin menu loop
    while True:
        show_options()
        choice = input("Select an option: ").strip()

        if choice == '1':
            reset_user_password()
        elif choice == '2':
            set_user_to_admin()
        elif choice == '3':
            update_aircraft_emissions()
        elif choice == '4':
            add_new_flight_route()
        elif choice == '5':
            print("Exiting Admin Dashboard.")
            sys.exit(0)
        else:
            print("Invalid option. Please try again.")

if __name__ == "__main__":
    main()