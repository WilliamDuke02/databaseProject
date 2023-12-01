import pandas as pd
import os
import sqlite3
import glob
import logging
import random

# Configure logging to save diagnostic information to 'logfile.log'
logging.basicConfig(filename='logfile.log', level=logging.DEBUG)

# Function to create a new SQLite database
def create_database(db_name):
    logging.info(f'Creating database: {db_name}')
    conn = sqlite3.connect(db_name)
    conn.close()

# Function to process a CSV file, merge it with a decoder, and save the results
def process_file(filename):
    logging.info(f'Starting process_file for {filename}')
    
    try:
        # Load VIN data and decoder CSV files
        vin_data = pd.read_csv(filename)
        vin_decoder = pd.read_csv('VIN_decoder.csv', encoding='latin1')

        # Extract relevant parts of VIN for merging
        vin_data['key1'] = vin_data.iloc[:, 0].astype(str).str[:8]
        vin_data['key2'] = vin_data.iloc[:, 0].astype(str).str[9]
        vin_decoder['key1'] = vin_decoder.iloc[:, 0].astype(str).str[:8]
        vin_decoder['key2'] = vin_decoder.iloc[:, 1].astype(str)

        # Perform the merge
        merged_df = pd.merge(
            vin_data,
            vin_decoder,
            left_on=['key1', 'key2'],
            right_on=['key1', 'key2'],
            how='inner'
        )

        # Drop temporary key columns
        merged_df.drop(columns=['key1', 'key2'], inplace=True)

        # Find unmerged rows
        merged_keys = merged_df.iloc[:, 0]
        unmerged_df = vin_data[~vin_data.iloc[:, 0].isin(merged_keys)]

        # Remove duplicates from merged data
        merged_df.drop_duplicates(subset=['VIN-NR'], keep='first', inplace=True)

        # Save the data to files
        merged_filename = f'merged_{os.path.basename(filename)}'
        unmerged_filename = f'unmerged_{os.path.basename(filename)}'

        merged_df.to_csv(merged_filename, index=False)
        unmerged_df.to_csv(unmerged_filename, index=False)

        logging.info(f'Saved merged data to {merged_filename}')
        logging.info(f'Saved unmerged data to {unmerged_filename}')
    
    except Exception as e:
        logging.error(f"An error occurred in the process_file function: {e}")

# Function to drop a specific column in CSV files
def drop_column_in_files(directory, file_pattern, column_index, column_name):
    pattern = os.path.join(directory, file_pattern)
    files = glob.glob(pattern)

    for file_path in files:
        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            continue

        if len(df.columns) > column_index and df.columns[column_index] == column_name:
            df.drop(df.columns[column_index], axis=1, inplace=True)
            try:
                df.to_csv(file_path, index=False)
                logging.info(f'Processed {file_path}')
            except Exception as e:
                logging.error(f'Error saving {file_path}: {e}')
        else:
            logging.warning(f'Skipped {file_path}: Column {column_index + 1} is not named "{column_name}" or does not exist')

# Function to import data from CSV files to an SQLite database
def import_to_db(directory, file_prefix, db_name):
    print(f'Importing data to database: {db_name}')
    conn = sqlite3.connect(db_name)

    # Iterate over CSV files in the directory with the specified prefix and extension
    for file in os.listdir(directory):
        if file.startswith(file_prefix) and file.endswith('.csv'):
            file_path = os.path.join(directory, file)
            try:
                df = pd.read_csv(file_path)
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
                continue

            # Import the DataFrame to the SQLite database
            table_name = os.path.splitext(file)[0]
            try:
                df.to_sql(table_name, conn, if_exists='append', index=False)
                print(f'Imported {file_path} to table {table_name}')
            except Exception as e:
                print(f"Error importing {file_path} to database: {e}")
                continue

    conn.close()

# Function to empty an SQLite database by dropping all tables
def empty_database(database_path):
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()

        # Get a list of all tables in the database
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        # Drop all tables in the database
        for table in tables:
            table_name = table[0]
            cursor.execute(f"DROP TABLE IF EXISTS {table_name};")

        # Commit the changes
        conn.commit()
        conn.close()
        print(f"SQLite database {database_path} emptied successfully.")
    except sqlite3.Error as e:
        print(f"Error emptying the SQLite database: {e}")

# Function to remove a file if it exists
def remove_file(file_path):
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            logging.info(f"Deleted {file_path}")
        except Exception as e:
            logging.error(f"Error deleting {file_path}: {e}")
    else:
        logging.warning(f"File not found: {file_path}")

# Function to create the 'merged_admin' table with a surrogate key
def create_merged_admin_table(cursor):
    cursor.execute('''
        CREATE TABLE merged_admin AS
        SELECT 
            "VIN-NR",
            "Vehicle Name",
            "Make",
            "Model-full" AS "Model_full",
            "Vehicle Manufacturer" AS "Vehicle_Manufacturer",
            "Technology",
            "Model Year" AS "Model_Year",
            "Date Added" AS "Date_Added",
            "Date Updated" AS "Date_Updated",
            "VIN_Key",
            "Vehicle Category" AS "Vehicle_Category",
            "Vehicle Use Case" AS "Vehicle_Use_Case",
            "Vehicle Class" AS "Vehicle_Class",
            CAST(ABS(RANDOM()) % 10 + 1 AS INTEGER) AS "Zip",
            CAST(ABS(RANDOM()) % 1000000 AS INTEGER) AS "Surrogate_Key"  -- Generate a unique surrogate key
        FROM merged_vins
    ''')

# Function to create the 'merged_nonadmin' table with the same surrogate key
def create_merged_nonadmin_table(cursor):
    cursor.execute('''
        CREATE TABLE merged_nonadmin AS
        SELECT 
            "Surrogate_Key",  -- Use the same surrogate key
            "Vehicle Name",
            "Make",
            "Model_full",
            "Vehicle_Manufacturer",
            "Technology",
            "Model_Year",
            "Date_Added",
            "Date_Updated",
            "VIN_Key",
            "Vehicle_Category",
            "Vehicle_Use_Case",
            "Vehicle_Class",
            "Zip"
        FROM merged_admin
    ''')

# Function to copy data from source databases to a target database with surrogate key
def copy_data_to_target_database_with_surrogate_key():
    # Connect to the source databases (merged_data.db and unmerged_data.db)
    conn_merged = sqlite3.connect('merged_data.db')
    conn_unmerged = sqlite3.connect('unmerged_data.db')

    # Connect to the target database (data.db)
    conn_target = sqlite3.connect('data.db')

    # Create cursor objects for source and target databases
    cursor_merged = conn_merged.cursor()
    cursor_unmerged = conn_unmerged.cursor()
    cursor_target = conn_target.cursor()

    # Attach the source databases as named databases
    cursor_target.execute("ATTACH DATABASE 'merged_data.db' AS source_merged")
    cursor_target.execute("ATTACH DATABASE 'unmerged_data.db' AS source_unmerged")

    # Create tables in the target database with the same surrogate key
    create_merged_admin_table(cursor_target)
    create_merged_nonadmin_table(cursor_target)

    # Copy the 'unmerged_vins' table from source_unmerged to target database
    cursor_target.execute("CREATE TABLE IF NOT EXISTS unmerged_vins AS SELECT *, ? AS Surrogate_Key FROM source_unmerged.unmerged_vins", (random.randint(1, 1000000),))

    # Commit and close connections
    conn_target.commit()
    conn_merged.close()
    conn_unmerged.close()
    conn_target.close()
    
# Function to perform cleanup by deleting temporary databases and tables
def cleanup_databases():
    try:
        # Delete the 'unmerged_data.db' database
        os.remove('unmerged_data.db')
        print("Deleted unmerged_data.db")

        # Delete the 'merged_data.db' database
        os.remove('merged_data.db')
        print("Deleted merged_data.db")

        # Connect to the 'data.db' database
        conn_data = sqlite3.connect('data.db')
        cursor_data = conn_data.cursor()

        # Remove the 'data' table from 'data.db'
        cursor_data.execute("DROP TABLE IF EXISTS data")
        conn_data.commit()
        conn_data.close()
        print("Removed 'data' table from data.db")
    except Exception as e:
        print(f"Error during cleanup: {e}")

# Main function to perform data processing and database operations
def main():
    # Empty the target databases
    empty_database('merged_data.db')
    empty_database('unmerged_data.db')
    empty_database('data.db')

    directory = '.'
    process_file('vins.csv')

    # Drop specified columns in CSV files
    drop_column_in_files(directory, 'merged_small_file_vins_*.xlsx', 3, 'MODEL')
    drop_column_in_files(directory, 'unmerged_small_file*.xlsx', 9, 'Model')

    # Create target databases
    create_database('merged_data.db')
    create_database('unmerged_data.db')

    # Import data from CSV files to target databases
    import_to_db(directory, 'merged_', 'merged_data.db')
    import_to_db(directory, 'unmerged_', 'unmerged_data.db')

    # Remove original CSV files
    remove_file('merged_vins.csv')
    remove_file('unmerged_vins.csv')

    # Connect to the merged_data.db database
    conn = sqlite3.connect('merged_data.db')
    cursor = conn.cursor()

    # Create 'merged_admin' table with surrogate key
    create_merged_admin_table(cursor)
    conn.commit()

    # Create 'merged_nonadmin' table with the same surrogate key
    create_merged_nonadmin_table(cursor)
    conn.commit()

    conn.close()
    print("Processing complete.")

# Entry point of the script
if __name__ == "__main__":
    main()  # Run the main function to process and create databases
    copy_data_to_target_database_with_surrogate_key()  # Run the data copying function with surrogate key
    cleanup_databases()  # Run the cleanup function
