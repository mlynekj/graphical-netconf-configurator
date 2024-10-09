# Other
import sqlite3, os

# TODO: vsechny printy predelat do nejakeho logovaciho souboru

# ---------------------------------------------- Creation of the DB ----------------------------------------------
def createConnection(db_file):
    # Create database connection to SQLite DB
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        if __debug__:
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
            device_type_id INTEGER PRIMARY KEY,
            type_name TEXT NOT NULL
        )
    ''')

    # Create Device Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Device (
            device_id TEXT PRIMARY KEY,
            device_type_id INTEGER NOT NULL,
            UNIQUE(device_id),
            FOREIGN KEY (device_type_id) REFERENCES DeviceType(device_type_id)
        )
    ''')

    # Create Connection Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Connection (
            connection_id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_a_id TEXT NOT NULL,
            device_b_id TEXT NOT NULL,
            cable_type TEXT,
            FOREIGN KEY (device_a_id) REFERENCES Device(device_id),
            FOREIGN KEY (device_b_id) REFERENCES Device(device_id)
        )
    ''')

    # Create DeviceAttribute Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS DeviceAttribute (
            attribute_id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL,
            attribute_key TEXT NOT NULL,
            attribute_value TEXT,
            FOREIGN KEY (device_id) REFERENCES Device(device_id)
        )
    ''')

    # Create Capabilities Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Capabilities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL,
            capability TEXT NOT NULL,
            FOREIGN KEY (device_id) REFERENCES Device(id)
        )
    ''')

    conn.commit()

    if __debug__:
        print("Tables created successfully.") # TODO: predelat do nejakeho logovaciho souboru

# ---------------------------------------------- Working with the contents of the DB ----------------------------------------------
def insertDeviceType(conn, type_name):
    #Insert a new device type
    cursor = conn.cursor()
    cursor.execute("INSERT INTO DeviceType (type_name) VALUES (?)", (type_name,))
    conn.commit()

    if __debug__:
        print(f"Inserted device type: {type_name}")

def insertDevice(conn, device_id, device_type_id):
    #Insert a new device into the Device table
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Device (device_id, device_type_id)
        VALUES (?, ?)
    """, (device_id, device_type_id))
    conn.commit()

    if __debug__:
        print(device_id)
        print(f"Inserted device: {device_id}")

def deleteDevice(conn, device_id):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Device WHERE device_id = ?", (device_id,))
    cursor.execute("DELETE FROM Capabilities WHERE device_id = ?", (device_id,))
    conn.commit()

    if __debug__:
        print(f"Deleted device: {device_id}")

def getDevice(conn, device_id):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Device WHERE device_type = ?", (device_id,))
    conn.commit()

    if __debug__:
        print(f"Selected device: {device_id}")

def insertConnection(conn, device_a_id, device_b_id, cable_type):
    #Insert a new connection between two devices
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Connection (device_a_id, device_b_id, cable_type)
        VALUES (?, ?, ?)
    """, (device_a_id, device_b_id, cable_type))
    conn.commit()
    
    if __debug__:
        print(f"Inserted connection between device {device_a_id} and {device_b_id}")


def insertDeviceAttribute(conn, device_id, attribute_key, attribute_value):
    #Insert an attribute for a device
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO DeviceAttribute (device_id, attribute_key, attribute_value)
        VALUES (?, ?, ?)
    """, (device_id, attribute_key, attribute_value))
    conn.commit()

    if __debug__:
        print(f"Inserted attribute {attribute_key} for device {device_id}")

def insertNetconfCapabilities(conn, capabilities, device_id):
    # Insert list of capabilities for a device
    cursor = conn.cursor()
    for capability in capabilities:
        cursor.execute("""
        INSERT INTO Capabilities (device_id, capability)
        VALUES (?, ?)
    """, (device_id, capability))
    conn.commit()

def queryNetconfCapabilities(conn, device_id):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT capability FROM Capabilities
        WHERE device_id = ?
    """, (device_id,))
    capabilities = cursor.fetchall()
    return [row[0] for row in capabilities]

def resetTables(conn):
    #Delete all rows in the tables related to devices and connections
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Connection")
    cursor.execute("DELETE FROM DeviceAttribute")
    cursor.execute("DELETE FROM Device")
    cursor.execute("DELETE FROM Capabilities")

    conn.commit()

    if __debug__:
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