import re
import mysql.connector
import sqlparse

def table_exists(cursor, table_name):
    """
    Check if a specific table exists in the database.
    """
    cursor.execute(f"""
        SELECT TABLE_NAME
        FROM information_schema.TABLES
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = '{table_name}';
    """)
    return cursor.fetchone() is not None

def import_table(cursor, table_statements):
    """
    Import statements for a specific table.
    """
    for statement in table_statements:
        try:
            cursor.execute(statement)
        except mysql.connector.Error as e:
            print(f"Error executing statement: {statement[:50]}... -> {e}")

def import_sql_dump(host, user, password, database, dump_file_path, quiet=True):
    connection = None  # Initialize connection
    try:
        # Connect to MySQL server (without specifying database)
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password
        )
        cursor = connection.cursor()

        # Ensure the database exists and use it
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database}")
        cursor.execute(f"USE {database}")
        if not quiet:
            print(f"Database '{database}' selected.")

        # Read the SQL dump file
        with open(dump_file_path, 'r', encoding='utf-8') as file:
            sql_dump = file.read()

        # Split dump by table using regex to identify table blocks
        tables = re.split(r"-- Table structure for table `([^`]+)`", sql_dump)

        for i in range(1, len(tables), 2):  # Step through the regex matches
            table_name = tables[i].strip()  # Extract table name
            table_content = tables[i + 1]  # Extract statements related to the table

            if not quiet:
                print(f"Processing table: {table_name}")

            # Check if the table already exists
            if table_exists(cursor, table_name):
                if not quiet:
                    print(f"Table '{table_name}' already exists. Skipping.")
                continue

            # Parse and execute the statements for the table
            table_statements = sqlparse.split(table_content)
            import_table(cursor, table_statements)

        # Commit changes
        connection.commit()
        cursor.execute("UNLOCK TABLES")
        if not quiet:
            print("SQL dump imported successfully, table by table.")

    except mysql.connector.Error as e:
        print(f"Database error: {e}")

    return cursor, connection


def show_tables(connection, cursor):
    try:
        # Execute the query to list all tables
        cursor.execute("SHOW TABLES")

        print("Tables in the database:")
        for table in cursor.fetchall():
            print(table[0])

    except mysql.connector.Error as err:
        print(f"Error: {err}")


def closeDBConnection(cursor, connection):
    # Ensure connection and cursor cleanup
    if connection and connection.is_connected():
        cursor.close()
        connection.close()
