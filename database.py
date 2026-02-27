import sqlite3
import os
from datetime import datetime

# The database file seen in your VS Code sidebar
DB_NAME = 'smc_urbanfix.db'

def get_db_connection():
    """Establish a connection to the SQLite database."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # Returns dictionary-like rows
    return conn

def init_db():
    """Initialize the database with the new 8-stage workflow schema."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create the main table for tracking defects
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS infrastructure_defects (
            record_id INTEGER PRIMARY KEY AUTOINCREMENT,
            defect_class TEXT NOT NULL,
            confidence REAL NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            severity TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            
            -- THE NEW WORKFLOW STATUS COLUMN --
            -- Allowed states: REPORTED, AI_ANALYZED, SMC_REVIEW, DEPT_ASSIGNED, 
            -- CONTRACTOR_ASSIGNED, REPAIRED, CITIZEN_VERIFIED, CLOSED
            status TEXT NOT NULL DEFAULT 'REPORTED',
            
            -- METADATA COLUMNS FOR THE NEW WORKFLOW --
            assigned_department TEXT,      -- e.g., 'PWD Road Engineering'
            contractor_name TEXT,          -- e.g., 'Acme Paving Co.'
            repair_image_url TEXT,         -- Image proof uploaded by contractor
            citizen_feedback TEXT          -- Notes from the CITIZEN_VERIFIED stage
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"[DB INFO] Initialized database '{DB_NAME}' with advanced workflow schema.")

def insert_defect(defect_class, confidence, lat, lon, severity):
    """
    Inserts a newly detected defect. 
    By default, it enters the workflow at the 'REPORTED' stage.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute('''
        INSERT INTO infrastructure_defects 
        (defect_class, confidence, latitude, longitude, severity, timestamp, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (defect_class, confidence, lat, lon, severity, timestamp, 'REPORTED'))
    
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id

def update_defect_status(record_id, new_status, **kwargs):
    """
    Moves the defect to the next stage in the workflow.
    Allows updating metadata (like assigned_department) simultaneously.
    """
    allowed_states = [
        'REPORTED', 'AI_ANALYZED', 'SMC_REVIEW', 'DEPT_ASSIGNED', 
        'CONTRACTOR_ASSIGNED', 'REPAIRED', 'CITIZEN_VERIFIED', 'CLOSED'
    ]
    
    if new_status not in allowed_states:
        raise ValueError(f"Invalid status. Must be one of: {allowed_states}")

    conn = get_db_connection()
    cursor = conn.cursor()

    # Base update query
    query = "UPDATE infrastructure_defects SET status = ?"
    params = [new_status]

    # Dynamically add metadata fields if they are passed in kwargs
    # Example: update_defect_status(1, 'DEPT_ASSIGNED', assigned_department='Water Dept')
    if 'assigned_department' in kwargs:
        query += ", assigned_department = ?"
        params.append(kwargs['assigned_department'])
    if 'contractor_name' in kwargs:
        query += ", contractor_name = ?"
        params.append(kwargs['contractor_name'])
    if 'repair_image_url' in kwargs:
        query += ", repair_image_url = ?"
        params.append(kwargs['repair_image_url'])
    if 'citizen_feedback' in kwargs:
        query += ", citizen_feedback = ?"
        params.append(kwargs['citizen_feedback'])

    query += " WHERE record_id = ?"
    params.append(record_id)

    cursor.execute(query, tuple(params))
    conn.commit()
    conn.close()
    
    return True

def get_all_defects():
    """Fetches all logs to display on the frontend System Logs table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM infrastructure_defects ORDER BY timestamp DESC')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# Run initialization when the script is imported/executed
if __name__ == '__main__':
    init_db()