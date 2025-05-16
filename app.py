import sqlite3
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

DATABASE_PATH = 'dashboard_data.db'

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # Access columns by name
    return conn

@app.route('/')
def index():
    """Serves the main dashboard HTML page."""
    return render_template('index.html')

@app.route('/api/filters', methods=['GET'])
def get_filter_options():
    """Fetches unique values for filter dropdowns."""
    conn = get_db_connection()
    cursor = conn.cursor()

    filters = {}
    filter_columns = ['end_year', 'topic', 'sector', 'region', 'pestle', 'source', 'country']

    for col in filter_columns:
        # Ensure column exists before querying
        cursor.execute(f"PRAGMA table_info(insights)")
        columns_info = cursor.fetchall()
        column_names = [info['name'] for info in columns_info]

        if col in column_names:
            # Query for distinct, non-null, non-empty values
            query = f"SELECT DISTINCT {col} FROM insights WHERE {col} IS NOT NULL AND {col} != '' ORDER BY {col}"
            if col in ['end_year']: # Numeric fields might need specific ordering or handling
                 query = f"SELECT DISTINCT {col} FROM insights WHERE {col} IS NOT NULL ORDER BY {col} DESC"
            
            cursor.execute(query)
            filters[col] = [row[col] for row in cursor.fetchall()]
        else:
            filters[col] = [] # Column doesn't exist, return empty list

    conn.close()
    return jsonify(filters)

@app.route('/api/data', methods=['GET'])
def get_dashboard_data():
    """Fetches data for the dashboard, applying filters from query parameters."""
    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT end_year, intensity, sector, topic, region, country, relevance, pestle, source, likelihood FROM insights WHERE 1=1"
    params = []

    # Available filters based on your data structure
    # Add more if needed and if they exist in your DB
    possible_filters = {
        'end_year': request.args.get('end_year'),
        'topic': request.args.get('topic'),
        'sector': request.args.get('sector'),
        'region': request.args.get('region'),
        'pestle': request.args.get('pestle'), # Corrected from PEST
        'source': request.args.get('source'),
        'country': request.args.get('country'),
        # 'city': request.args.get('city'), # Add if city data is available and relevant
        # 'swot': request.args.get('swot'), # Add if swot data is available
    }

    for column, value in possible_filters.items():
        if value: # If a filter value is provided
            # Check if column exists in the table to prevent SQL injection via column names
            cursor.execute(f"PRAGMA table_info(insights)")
            columns_info = cursor.fetchall()
            column_names = [info['name'] for info in columns_info]
            if column in column_names:
                query += f" AND {column} = ?"
                params.append(value)
            else:
                # Optionally log a warning or handle unknown filter columns
                print(f"Warning: Filter column '{column}' not found in table 'insights'.")


    cursor.execute(query, tuple(params))
    data = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(data)

if __name__ == '__main__':
    # You might need to run the data_setup.py script first if the DB doesn't exist or is empty.
    # Check if db exists, if not, guide user.
    import os
    if not os.path.exists(DATABASE_PATH):
        print(f"Database file '{DATABASE_PATH}' not found.")
        print("Please run the 'data_setup.py' script first to create and populate the database.")
    else:
        app.run(debug=True, port=5001) # Changed port to 5001 to avoid common conflicts
