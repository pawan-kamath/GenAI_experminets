import os
import sqlite3

import psycopg2
import psycopg2.extras


def connect_db(db_type="sqlite", credentials=None):
    """Connect to the specified database."""
    if db_type == "sqlite":
        db_path = credentials.get("db_path", "data/chinook.db")
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"SQLite database file not found at {db_path}")
        conn = sqlite3.connect(db_path)
        return conn
    elif db_type == "postgresql":
        try:
            conn = psycopg2.connect(
                host=credentials["host"],
                port=credentials["port"],
                database=credentials["database"],
                user=credentials["user"],
                password=credentials["password"],
            )
            return conn
        except Exception as e:
            raise ConnectionError(
                f"Unable to connect to the PostgreSQL database: {str(e)}"
            )
    else:
        raise ValueError("Unsupported database type. Use 'sqlite' or 'postgresql'.")


def get_table_names(conn, db_type, schema_name=""):
    """Return a list of table names for SQLite or PostgreSQL."""
    table_names = []
    if db_type == "sqlite":
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
        )
        for table in cursor.fetchall():
            table_names.append(table[0])
    elif db_type == "postgresql":
        cursor = conn.cursor()
        # Uses the schema_name filter if provided
        cursor.execute(
            """
            SELECT tablename
            FROM pg_catalog.pg_tables
            WHERE schemaname = %s
            ORDER BY tablename;
        """,
            (schema_name,),
        )
        tables = cursor.fetchall()
        cursor.close()
        return [table[0] for table in tables]
    return table_names


def get_column_names(conn, table_name, db_type, schema_name=""):
    """Return a list of column names for a given table in SQLite or PostgreSQL."""
    column_details = []

    if db_type == "sqlite":
        query = f"PRAGMA table_info('{table_name}');"
        cursor = conn.execute(query)
        print(cursor.fetchall())
        for column in cursor.fetchall():
            column_details.append(
                {
                    "column_name": column[1],
                    "data_type": column[2],
                    "not_null": bool(column[3]),
                    "default_value": column[4],
                }
            )

    elif db_type == "postgresql":
        cursor = conn.cursor()
        query = """
            SELECT column_name,
                   data_type,
                   character_maximum_length,
                   is_nullable
            FROM information_schema.columns
            WHERE table_name = %s
            AND table_schema = %s;
        """
        cursor.execute(query, (table_name, schema_name))
        fetched_columns = cursor.fetchall()
        for column in fetched_columns:
            column_details.append(
                {
                    "column_name": column[0],
                    "data_type": column[1],
                    "max_length": column[2],
                    "is_nullable": column[3],
                }
            )
        cursor.close()

    return column_details


def get_foreign_key_constraints(conn, db_type, schema_name=""):
    """Return a list of foreign key constraints for PostgreSQL."""
    if db_type != "postgresql":
        return []  # Only implemented for PostgreSQL

    cursor = conn.cursor()
    query = """
        SELECT
            conname AS constraint_name,
            conrelid::regclass AS table_name,
            a.attname AS column_name,
            confrelid::regclass AS foreign_table_name,
            af.attname AS foreign_column_name
        FROM
            pg_constraint AS c
        JOIN
            pg_attribute AS a ON a.attnum = ANY(c.conkey) AND a.attrelid = c.conrelid
        JOIN
            pg_attribute AS af ON af.attnum = ANY(c.confkey) AND af.attrelid = c.confrelid
        WHERE
            contype = 'f' AND connamespace = %s::regnamespace
        ORDER BY table_name, constraint_name;
    """

    try:
        cursor.execute(query, (schema_name,))
        fk_constraints = cursor.fetchall()
        cursor.close()

        fk_details = []
        for fk in fk_constraints:
            # Remove schema prefix from table names for cleaner display
            table_name = fk[1].split(".")[-1] if "." in str(fk[1]) else str(fk[1])
            foreign_table_name = (
                fk[3].split(".")[-1] if "." in str(fk[3]) else str(fk[3])
            )

            fk_details.append(
                {
                    "constraint_name": fk[0],
                    "table_name": table_name,
                    "column_name": fk[2],
                    "foreign_table_name": foreign_table_name,
                    "foreign_column_name": fk[4],
                }
            )

        return fk_details
    except Exception as e:
        cursor.close()
        print(f"Error fetching foreign key constraints: {e}")
        return []


def get_database_schema(conn, db_type, schema=""):
    """
    Return a detailed representation of the database schema including foreign key relationships.

    For PostgreSQL databases, this function now includes:
    - Table and column information
    - Foreign key constraints for each table
    - A summary of all foreign key relationships

    Args:
        conn: Database connection object
        db_type: Database type ('sqlite' or 'postgresql')
        schema: Schema name (required for PostgreSQL)

    Returns:
        str: Formatted schema information including FK relationships
    """
    schema_lines = []
    table_names = get_table_names(conn, db_type, schema)

    # Get foreign key constraints for the entire schema (PostgreSQL only)
    fk_constraints = get_foreign_key_constraints(conn, db_type, schema)

    # Group foreign keys by table for easier lookup
    fk_by_table = {}
    for fk in fk_constraints:
        table_name = fk["table_name"]
        if table_name not in fk_by_table:
            fk_by_table[table_name] = []
        fk_by_table[table_name].append(fk)

    for table_name in table_names:
        columns = get_column_names(conn, table_name, db_type, schema)
        column_info = []

        for col in columns:
            if db_type == "postgresql":
                column_desc = (
                    f"{col['column_name']} {col['data_type']} "
                    f"(Nullable: {col['is_nullable']}, Max Length: {col['max_length']})"
                )
            else:
                # SQLite format
                column_desc = (
                    f"{col['column_name']} {col['data_type']} "
                    f"(Not Null: {col['not_null']}, Default: {col['default_value']})"
                )
            column_info.append(column_desc)

        if schema:
            header = f"Schema: {schema}\nTable: {table_name}\nColumns:\n  "
        else:
            header = f"Table: {table_name}\nColumns:\n  "

        table_info = header + "\n  ".join(column_info)

        # Add foreign key information if available
        if table_name in fk_by_table:
            fk_info = []
            for fk in fk_by_table[table_name]:
                fk_desc = (
                    f"{fk['column_name']} -> {fk['foreign_table_name']}.{fk['foreign_column_name']} "
                    f"(Constraint: {fk['constraint_name']})"
                )
                fk_info.append(fk_desc)

            table_info += "\nForeign Keys:\n  " + "\n  ".join(fk_info)

        schema_lines.append(table_info)

    # Add a summary of all foreign key relationships at the end
    if fk_constraints and db_type == "postgresql":
        fk_summary = ["\n=== Foreign Key Relationships Summary ==="]
        for fk in fk_constraints:
            fk_summary.append(
                f"{fk['table_name']}.{fk['column_name']} -> "
                f"{fk['foreign_table_name']}.{fk['foreign_column_name']}"
            )
        schema_lines.append("\n".join(fk_summary))

    return "\n\n".join(schema_lines)


def execute_query(conn, query):
    """Execute an SQL query and return the results."""
    try:
        cursor = conn.execute(query)
        results = cursor.fetchall()
        column_names = (
            [description[0] for description in cursor.description]
            if cursor.description
            else []
        )
        return results, column_names
    except Exception as e:
        return str(e), None


def ask_database(conn, query, db_type):
    """Function to query database with a provided SQL query."""
    # Allow only SELECT queries
    if not query.strip().upper().startswith("SELECT"):
        return "Only SELECT queries are allowed."

    try:
        if db_type == "sqlite":
            cursor = conn.execute(query)
            results = cursor.fetchall()
            column_names = (
                [description[0] for description in cursor.description]
                if cursor.description
                else []
            )
        elif db_type == "postgresql":
            cursor = conn.cursor()
            cursor.execute(query)
            results = cursor.fetchall()
            column_names = [desc.name for desc in cursor.description]
            cursor.close()
        else:
            return "Unsupported database type."

        # Format results as a list of dictionaries
        result_dicts = [dict(zip(column_names, row)) for row in results]
        return result_dicts
    except Exception as e:
        return str(e)


def get_foreign_key_relationships(conn, db_type, schema_name=""):
    """Return a formatted string of foreign key relationships for easy reading by AI assistants."""
    if db_type != "postgresql":
        return "Foreign key relationships are only supported for PostgreSQL databases."

    fk_constraints = get_foreign_key_constraints(conn, db_type, schema_name)

    if not fk_constraints:
        return f"No foreign key relationships found in schema '{schema_name}'."

    relationships = [f"Foreign Key Relationships in Schema '{schema_name}':\n"]
    relationships.append("=" * 50)

    for fk in fk_constraints:
        relationships.append(
            f"• {fk['table_name']}.{fk['column_name']} "
            f"references {fk['foreign_table_name']}.{fk['foreign_column_name']} "
            f"(constraint: {fk['constraint_name']})"
        )

    return "\n".join(relationships)
