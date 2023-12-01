Introduction
The Vehicle Database Management System is a comprehensive application designed for managing extensive vehicle data. It's tailored for entities like the Department of Transportation (DOT) and Department of Energy (DOE) to assist in infrastructure planning and decision-making. The system uses Python, SQLite, and Tkinter for its operations.

Pre-requisites
Python 3.7 or higher
SQLite3
Tkinter (usually comes pre-installed with Python)
Matplotlib (for graphing functionalities)
Installation and Setup
Clone or Download the Project: Get the project files from the provided source. This will include make_ui.py, reset_dbs.py, and a database file data.db.

Install Required Libraries: If not already installed, you can install matplotlib using pip:

Copy code
pip install matplotlib
Setting Up the Database: Run reset_dbs.py to set up or reset the database to its initial state. This script creates the necessary tables and populates them with sample data.

Running the Application
Starting the Application: Open your terminal or command prompt, navigate to the project directory, and run:

Copy code
python make_ui.py
This will launch the main login window of the application.

Logging In:

As an Admin: Use username admin and password admin123.
As a Guest: Use username guest without a password.
Using the Application:

Admin Access: Admin users can add, update, remove, export, and graph data from the merged_admin, merged_nonadmin, and unmerged_vins tables.
Guest Access: Guest users have read-only access to the merged_nonadmin table and can export and graph data.
Executing Test Queries
The application includes various functionalities that act as test queries. Here are five key operations to test the database:

Add Data: Admins can add new vehicle data to any table. For instance, adding a new entry to merged_nonadmin.

Update Data: Modify an existing record. For example, updating the Make of a vehicle in the merged_admin table.

Export Data: Export selected data from merged_nonadmin or unmerged_vins into a CSV file.

Generate Graphs: Create pie or bar charts based on data in merged_nonadmin. For instance, generating a pie chart for vehicle distribution by technology type.

Delete Data: Remove an entry from a table, like deleting a record from unmerged_vins.