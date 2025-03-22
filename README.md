# Flight Emissions Tracker

Welcome to the Flight Emissions Tracker! This application helps users calculate, log, and analyze carbon emissions from air travel. It includes two command-line programs—one for client (end-user) operations and another for administrative tasks—and a set of SQL files to create and manage the underlying MySQL database.

---

## Table of Contents
1. [Project Overview](#project-overview)
2. [Repository Structure](#repository-structure)
3. [Prerequisites](#prerequisites)
4. [Setting Up the Database](#setting-up-the-database)
5. [Running the Applications](#running-the-applications)
6. [Important Notes](#important-notes)
7. [Preloaded Admin User and Sample Data](#preloaded-admin-user-and-sample-data)
8. [Reflection and Additional Documentation](#reflection-and-additional-documentation)
9. [Contact](#contact)

---

## Project Overview

This Flight Emissions Tracker stores flight route information (airports, aircraft, etc.) and logs user trips, providing estimates of CO₂ emissions for each trip. Users can:
- Look up airports and routes.
- Calculate carbon emissions for specific flights.
- Insert, edit, or delete trip data.
- View their trip history and aggregated emissions.

Administrators can:
- Reset or grant privileges to users.
- Update aircraft emissions data.
- Add or modify flight routes.
- Manage overall database integrity.

The system aims to raise awareness about the environmental impact of air travel and provide meaningful insights for users.

---

## Repository Structure

```
final_project/
├── data/
│   ├── aircrafts.csv
│   ├── airports.csv
│   ├── routes.csv
│   └── countries.csv
├── figures/
│   ├── emissions_er_model.png
│   ├── milestone_er_model.png
│   ├── proposal_er_model.png
│   ├── emissions_user_flowchart.png
│   ├── milestone_user_flowchart.png
│   ├── proposal_user_flowchart.png
│   └── emissions_admin_flowchart.png
├── app-admin.py          # Admin command-line application (Part J)
├── app-client.py         # Client command-line application (Part J)
├── grant-permissions.sql # Grants user privileges in the DB (Part F)
├── link-to-submission.txt # (Required in 25wi) links to data or diagrams
├── load-data.sql         # Loads CSV data into your DB tables (Part D)
├── queries.sql           # Sample queries for testing (Part H)
├── README.md             # This README (Part K)
├── reflection.pdf        # Reflection on design & implementation (Parts A, B, G, L)
├── setup-passwords.sql   # Basic password management for the DB (Part E)
├── setup-routines.sql    # Creates stored routines and triggers (Part I)
└── setup.sql             # Main DDL to create your schema (Part B)
```

- **`data/`**: Contains all CSV files used by `load-data.sql`.
- **`figures/`**: Holds ER diagrams and flowcharts (PNGs/JPEGs).
- **`reflection.pdf`**: Written reflection, including diagrams, relational algebra, and index justifications.

---

## Prerequisites

1. **MySQL** (version 5.7+ or 8.x recommended)
   - Ensure that the `mysql` command is available in your terminal.
   - You need a MySQL root user (or any user with privileges to create databases and users).

2. **Python 3** (version 3.6+ recommended)  
   - You will need the following Python modules installed:
     ```python
     import sys               # Built-in, for error messages, etc.
     import mysql.connector   # MySQL connector for Python
     import pandas as pd      # Data manipulation
     from tabulate import tabulate  # For pretty-printing tables
     from datetime import datetime  # Built-in, for date/time
     ```
     If any import fails, install or update the corresponding package, for example:
     ```bash
     pip install mysql-connector-python
     pip install pandas
     pip install pyarrow
     pip install tabulate
     ```
   - The application has been tested on Python 3.x.

3. **Git** (optional but recommended)
   - To clone or fork this repository.

---

## Setting Up the Database

Follow these steps in a terminal. The order of operations is important:

1. **Clone or download** this repository (if not already done):
   ```bash
   git clone <URL_to_this_repo>
   cd flight-emissions-tracker
   ```

2. **Start MySQL** from within this directory:
   ```bash
   mysql --local-infile=1 -u root -p
   ```
   - Enter your MySQL root password when prompted.

3. Create the `tripsdb` database**:
   ```sql
   SHOW DATABASES; -- to check if this database exists
   DROP DATABASE tripsdb; -- if database already exists
   CREATE DATABASE tripsdb;
   ```

4. Select the `tripsdb`:
   ```sql
   USE tripsdb;
   ```

4. **Run each SQL file in order**:
   ```sql
   source setup.sql;            -- Part B: Creates tables, views, etc.
   source setup-passwords.sql;  -- Part E: Basic password management
   source setup-routines.sql;   -- Part I: Stored routines and triggers
   source load-data.sql;        -- Part D: Loads CSV data into tables
   source grant-permissions.sql;-- Part F: Creates additional users and grants privileges
   source queries.sql;          -- Part H: Check that queries run with no errors/warnings
   ```
   - You may see “DROP ... IF EXISTS” warnings; these are safe to ignore.

5. **Quit MySQL**:
   ```sql
   quit;
   ```

Your database should now be initialized with all tables, data, and stored routines set up properly.

---

## Running the Applications

After setting up the database, you can run either of the command-line applications:

1. **Client Application** (for end-users):
   ```bash
   python3 app-client.py
   ```
   - Follow the on-screen prompts to log in, view or create trips, calculate emissions, etc.

2. **Admin Application** (for administrators):
   ```bash
   python3 app-admin.py
   ```
   - Perform tasks like user password resets, granting privileges, updating aircraft information, and so on.

If you run into any issues, ensure your database credentials and connection details match those in the Python source files, specifically in `get_conn()`.

---

## Important Notes

- **Database Credentials**:  
  Make sure the credentials in `app-client.py` and `app-admin.py` match any created users from `grant-permissions.sql`. You may need to adapt the host, port, username, or password depending on your local MySQL setup.

- **Data Files & Routes Information**:  
  - The data/ folder includes CSV files that are loaded by `load-data.sql`. If you rename or move these files, update the `LOAD DATA` statements accordingly.
  - The flight routes are current as of **2014**. Administrators can still update routes via the admin interface as needed.

- **Warnings**:  
  It is normal to see warnings about dropping tables or routines that do not exist yet (e.g., `DROP TABLE IF EXISTS`). No other SQL warnings should appear.

- **Figures**:  
  ER diagrams and flowcharts are in the `figures/` directory. Refer to them for a visual guide to the database schema and application flow.

---

## Preloaded Admin User and Sample Data

I have **preloaded** an **admin** user in the database with the following credentials:
- **Username:** `adminuser`
- **Password:** `securepass123`

This account works in **both** `app-client.py` and `app-admin.py`. Because it is already set up as an administrator, you can log in and:
- Create or reset other user accounts.
- Grant admin privileges to newly created accounts.

Additionally, the `adminuser` account has **10 sample trips** loaded under its client profile. You can view these trips within `app-client.py` to explore the application’s core functionality (i.e. listing trips and aggregating by country, year, or month) and get a feel for how the system behaves with real data (trips based on my recent trips in the past few years).

---

## Reflection and Additional Documentation

- **`reflection.pdf`** (Parts A, C, G, L) contains:
  - ER diagrams
  - Relational algebra justifications
  - Index discussions
  - Overall project reflection (challenges, successes, future improvements)

- **`link-to-submission.txt`**:  
  All links to data sources, high-res diagrams, additional documentation, and the full code on GitHub is place here.

---

## Contact

For questions, please reach out to the repository owner at tabraham@caltech.edu or open an issue in this GitHub repository. We hope you find this Flight Emissions Tracker useful and educational!

---

**End of README**
