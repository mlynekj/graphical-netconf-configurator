import sqlite3, os

# TODO: vsechny printy predelat do nejakeho logovaciho souboru

# ---------------------------------------------- Creation of the DB ----------------------------------------------
def createConnection(db_file):
    # Create database connection to SQLite DB
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print("Connection established to SQLite DB")
        return conn
    except sqlite3.Error as e:
        print(e)
    return conn

def createTables(conn):
    # Create tables for the device management
    cursor = conn.cursor()
    
    # Create DeviceType Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS DeviceType (
            device_type_id INTEGER PRIMARY KEY AUTOINCREMENT,
            type_name TEXT NOT NULL
        )
    ''')

    # Create Device Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Device (
            device_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            device_type_id INTEGER NOT NULL,
            UNIQUE(name),
            FOREIGN KEY (device_type_id) REFERENCES DeviceType(device_type_id)
        )
    ''')

    # Create Connection Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Connection (
            connection_id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_a_id INTEGER NOT NULL,
            device_b_id INTEGER NOT NULL,
            cable_type TEXT,
            FOREIGN KEY (device_a_id) REFERENCES Device(device_id),
            FOREIGN KEY (device_b_id) REFERENCES Device(device_id)
        )
    ''')

    # Create DeviceAttribute Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS DeviceAttribute (
            attribute_id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id INTEGER NOT NULL,
            attribute_key TEXT NOT NULL,
            attribute_value TEXT,
            FOREIGN KEY (device_id) REFERENCES Device(device_id)
        )
    ''')

    conn.commit()
    print("Tables created successfully.") # TODO: predelat do nejakeho logovaciho souboru

# ---------------------------------------------- Working with the contents of the DB ----------------------------------------------
def insertDeviceType(conn, type_name):
    #Insert a new device type
    cursor = conn.cursor()
    cursor.execute("INSERT INTO DeviceType (type_name) VALUES (?)", (type_name,))
    conn.commit()
    print(f"Inserted device type: {type_name}")

def insertDevice(conn, name, device_type_id):
    #Insert a new device into the Device table
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Device (name, device_type_id)
        VALUES (?, ?)
    """, (name, device_type_id))
    conn.commit()
    print(f"Inserted device: {name}")

def insertConnection(conn, device_a_id, device_b_id, cable_type):
    #Insert a new connection between two devices
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Connection (device_a_id, device_b_id, cable_type)
        VALUES (?, ?, ?)
    """, (device_a_id, device_b_id, cable_type))
    conn.commit()
    print(f"Inserted connection between device {device_a_id} and {device_b_id}")


def insertDeviceAttribute(conn, device_id, attribute_key, attribute_value):
    #Insert an attribute for a device
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO DeviceAttribute (device_id, attribute_key, attribute_value)
        VALUES (?, ?, ?)
    """, (device_id, attribute_key, attribute_value))
    conn.commit()
    print(f"Inserted attribute {attribute_key} for device {device_id}")

def resetTables(conn):
    #Delete all rows in the tables related to devices and connections
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Connection")
    cursor.execute("DELETE FROM DeviceAttribute")
    cursor.execute("DELETE FROM Device")

    conn.commit()
    print("All device-related data has been deleted.")


# ---------------------------------------------- Initializing the database ----------------------------------------------
connection = createConnection("devices.db")
createTables(connection)
resetTables(connection)

#DeviceType table
device_types = ['Router', 'Switch', 'PC']

cursor = connection.cursor()
cursor.execute("SELECT COUNT(*) FROM deviceType")
if cursor.fetchone()[0] == 0: # If the table is empty
    for device_type in device_types:
        insertDeviceType(connection, device_type)