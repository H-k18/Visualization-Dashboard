import json
import sqlite3

# --- Configuration ---
JSON_FILE_PATH = 'jsondata.json'
DB_FILE_PATH = 'dashboard_data.db'
TABLE_NAME = 'insights'

def create_table(conn):
    """Creates the insights table in the SQLite database."""
    cursor = conn.cursor()
    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        end_year INTEGER,
        intensity INTEGER,
        sector TEXT,
        topic TEXT,
        insight TEXT,
        url TEXT,
        region TEXT,
        start_year INTEGER,
        impact INTEGER,
        added TEXT,
        published TEXT,
        country TEXT,
        relevance INTEGER,
        pestle TEXT,
        source TEXT,
        title TEXT,
        likelihood INTEGER
    )
    """)
    conn.commit()
    print(f"Table '{TABLE_NAME}' created successfully or already exists.")

def clean_value(value, target_type="text"):
    """Cleans and converts value, handling empty strings for numeric types."""
    if isinstance(value, str) and not value.strip():
        return None  # Convert empty strings to None (NULL in SQL)
    if target_type == "integer":
        try:
            return int(value) if value is not None else None
        except (ValueError, TypeError):
            return None # If conversion fails, return None
    return value

def populate_database(conn, data):
    """Populates the database with data from the JSON file."""
    cursor = conn.cursor()
    insert_count = 0
    skipped_count = 0

    for record in data:
        # Ensure all expected keys exist, providing None if missing
        # Also clean values, especially for numeric fields
        values = (
            clean_value(record.get('end_year'), 'integer'),
            clean_value(record.get('intensity'), 'integer'),
            clean_value(record.get('sector')),
            clean_value(record.get('topic')),
            clean_value(record.get('insight')),
            clean_value(record.get('url')),
            clean_value(record.get('region')),
            clean_value(record.get('start_year'), 'integer'),
            clean_value(record.get('impact'), 'integer'), # Assuming impact can be numeric
            clean_value(record.get('added')),
            clean_value(record.get('published')),
            clean_value(record.get('country')),
            clean_value(record.get('relevance'), 'integer'),
            clean_value(record.get('pestle')),
            clean_value(record.get('source')),
            clean_value(record.get('title')),
            clean_value(record.get('likelihood'), 'integer')
        )

        try:
            cursor.execute(f"""
            INSERT INTO {TABLE_NAME} (
                end_year, intensity, sector, topic, insight, url, region,
                start_year, impact, added, published, country, relevance,
                pestle, source, title, likelihood
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, values)
            insert_count += 1
        except sqlite3.InterfaceError as e:
            print(f"Skipping record due to error: {e}. Record: {record}")
            skipped_count += 1
        except Exception as e:
            print(f"An unexpected error occurred for record: {record}. Error: {e}")
            skipped_count +=1


    conn.commit()
    print(f"Successfully inserted {insert_count} records.")
    if skipped_count > 0:
        print(f"Skipped {skipped_count} records due to errors or missing critical data.")

def main():
    """Main function to orchestrate database setup and population."""
    # Load data from JSON file
    try:
        with open(JSON_FILE_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"Successfully loaded data from '{JSON_FILE_PATH}'. Found {len(data)} records.")
    except FileNotFoundError:
        print(f"Error: JSON file '{JSON_FILE_PATH}' not found.")
        print("Please ensure 'jsondata.json' is in the same directory as this script.")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{JSON_FILE_PATH}'. Please check its format.")
        return

    # Connect to SQLite database (or create it if it doesn't exist)
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE_PATH)
        print(f"Successfully connected to database '{DB_FILE_PATH}'.")

        # Create table
        create_table(conn)

        # Check if table is already populated
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}")
        count = cursor.fetchone()[0]

        if count > 0:
            print(f"Table '{TABLE_NAME}' already contains {count} records. Skipping population.")
            user_choice = input("Do you want to clear existing data and repopulate? (yes/no): ").strip().lower()
            if user_choice == 'yes':
                print("Clearing existing data...")
                cursor.execute(f"DELETE FROM {TABLE_NAME}")
                conn.commit()
                print("Existing data cleared. Repopulating...")
                populate_database(conn, data)
            else:
                print("Exiting without repopulating.")
        else:
            # Populate database
            populate_database(conn, data)

    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
    finally:
        if conn:
            conn.close()
            print(f"Database connection to '{DB_FILE_PATH}' closed.")

if __name__ == '__main__':
    main()
