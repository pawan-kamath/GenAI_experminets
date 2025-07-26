import base64
import json
import logging
import os
import threading

import openai
import requests
from config import Config
from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, request, url_for
from openai import AzureOpenAI
from tabulate import tabulate
from tools.utils import ask_database, connect_db, get_database_schema

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.config.from_object(Config)

# Azure OpenAI settings

client = AzureOpenAI(
    api_key=app.config["OPENAI_API_KEY"],
    api_version="2024-07-01-preview",
    azure_endpoint=app.config["OPENAI_API_HOST"],
)

# Path to your SQLite database
DATABASE_PATH = os.environ.get("SQLITE_DB_PATH", os.path.join("data", "chinook.db"))

# Global variables
conversation_histories = {}
conversation_lock = threading.Lock()
database_schema_string = ""
database_schema_lock = threading.Lock()

current_db_credentials = None
conversation_histories = {}
database_schema_string = ""


def initialize_default_db():
    global current_db_credentials, database_schema_string
    current_db_credentials = {"db_type": "sqlite", "db_path": DATABASE_PATH}
    conn = connect_db(db_type="sqlite", credentials=current_db_credentials)
    database_schema_string = get_database_schema(conn, "sqlite")
    conn.close()


# Call this function during app startup
initialize_default_db()


def execute_sql_function(query, db_type):
    """Wrapper function to be called by the assistant."""
    print(db_type)
    conn = connect_db(db_type=db_type, credentials=current_db_credentials)
    response = ask_database(conn, query, db_type)
    if isinstance(response, list):
        # If response is a list of dictionaries, format it into a markdown table
        if response:
            headers = response[0].keys()
            rows = [list(item.values()) for item in response]
            # Use tabulate to format as a table
            table = tabulate(rows, headers=headers, tablefmt="github")
            return table
        else:
            return "No results found."
    elif isinstance(response, dict) and "error" in response:
        return response["error"]
    else:
        return str(response)


def execute_api_call(params, db_type):
    """Function to make API calls to ServiceNow."""
    # Get credentials and API details from current_db_credentials
    api_base_url = current_db_credentials["host"]
    api_endpoint = "/api/now/table/problem"  # Default endpoint
    username = current_db_credentials["user"]
    password = current_db_credentials["password"]

    # Build full URL
    full_url = api_base_url.rstrip("/") + "/" + api_endpoint.lstrip("/")

    # Encode credentials for Basic Auth
    credentials = f"{username}:{password}"
    b64Val = base64.b64encode(credentials.encode()).decode()
    headers = {"Authorization": f"Basic {b64Val}", "Content-Type": "application/json"}

    try:
        response = requests.get(full_url, headers=headers, params=params, verify=False)
        response.raise_for_status()
        data = response.json()
        # Extract relevant information from the response
        if "result" in data:
            result = data["result"]
            if isinstance(result, list):
                if not result:
                    return "No results found."
                # Return as a formatted table
                table_headers = result[0].keys()
                rows = [list(item.values()) for item in result]
                table = tabulate(rows, headers=table_headers, tablefmt="github")
                return table
            else:
                # Return the single result as a JSON string
                return json.dumps(result, indent=2)
        else:
            return "No results found."
    except Exception as e:
        return f"An error occurred during the API call: {str(e)}"


def debug_sql_query_function(query, error_message, db_type):
    """Function to debug and correct an SQL query based on the error message."""
    correction_prompt = f"""
    The following SQL query resulted in an error when executed against a {db_type} database:

    Query:
    {query}

    Error message:
    {error_message}

    Please provide a corrected SQL query that fixes the error, considering the database schema below.
    Ensure the corrected query is valid for a {db_type} database and does not modify any data.

    Database Schema:
    {database_schema_string}
    """

    messages = [{"role": "user", "content": correction_prompt}]

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Use the same model
            messages=messages,
        )
        corrected_query = response.choices[0].message.content.strip()  # Get the corrected query
        return corrected_query
    except Exception as e:
        return f"I couldn't correct the query due to an error: {e}"


# Map function names to functions
function_mappings = {
    "execute_sql_function": execute_sql_function,
    "debug_sql_query": debug_sql_query_function,
    "execute_api_call": execute_api_call,
}


@app.route("/connect", methods=["GET", "POST"])
def connect():
    global current_db_credentials, database_schema_string
    if request.method == "POST":
        db_type = request.form.get("db_type", "postgresql")
        host = request.form["host"]
        port = request.form["port"]
        database = request.form["database"]
        user = request.form["user"]
        password = request.form["password"]
        schema_name = request.form["schema"]

        # Update global database credentials
        current_db_credentials = {
            "db_type": db_type,
            "host": host,
            "port": port,
            "database": database,
            "user": user,
            "password": password,
        }

        # Try to connect to the new database
        try:
            conn = connect_db(db_type=db_type, credentials=current_db_credentials)
            print("Connection succesful")
            new_database_schema_string = get_database_schema(conn, db_type, schema_name)
            conn.close()
        except Exception as e:
            error_message = f"Failed to connect to the database: {str(e)}"
            return render_template("connect.html", error=error_message)

        # Update the global schema and clear conversation history
        with database_schema_lock:
            database_schema_string = new_database_schema_string
        with conversation_lock:
            conversation_histories.clear()

        return redirect(url_for("chat_page"))
    else:
        return render_template("connect.html")


@app.route("/connect_snow", methods=["GET", "POST"])
def connect_snow():
    global current_db_credentials, database_schema_string
    if request.method == "POST":
        db_type = request.form.get("db_type", "servicenow")
        api = request.form["api"]
        user = request.form["user"]
        password = request.form["password"]

        # Update global credentials
        current_db_credentials = {"db_type": db_type, "host": api, "user": user, "password": password}

        # For simplicity, we'll assume the connection is always successful
        print("Connection successful")
        with conversation_lock:
            conversation_histories.clear()

        return redirect(url_for("chat_page"))
    else:
        return render_template("connect_snow.html")


# Route for the index page
@app.route("/")
def index():
    return redirect(url_for("chat_page"))


# Route for the chat page
@app.route("/chat_page")
def chat_page():
    db_type = current_db_credentials.get("db_type")

    if db_type == "postgresql":
        db_name = current_db_credentials.get("database", "Unknown")
    elif db_type == "sqlite":
        db_name = os.path.basename(current_db_credentials.get("db_path", "Unknown"))
    elif db_type == "servicenow":
        db_name = current_db_credentials.get("instance_name", "ServiceNow")
    else:
        db_name = "Unknown"

    # Get all database names from the configuration to pass to the client
    postgres_db_name = app.config["POSTGRESQL_CONFIG"].get("database", "Unknown")
    sqlite_db_name = os.path.basename(DATABASE_PATH)
    servicenow_instance_name = app.config["SERVICENOW_CONFIG"].get("instance_name", "ServiceNow")

    # Check if configurations are available
    postgres_available = all(app.config["POSTGRESQL_CONFIG"].values())
    servicenow_available = all(app.config["SERVICENOW_CONFIG"].values())

    return render_template(
        "index.html",
        db_type=db_type,
        db_name=db_name,
        postgres_available=postgres_available,
        servicenow_available=servicenow_available,
        postgres_db_name=postgres_db_name,
        sqlite_db_name=sqlite_db_name,
        servicenow_instance_name=servicenow_instance_name,
    )


@app.route("/connect_env", methods=["POST"])
def connect_env():
    global current_db_credentials, database_schema_string

    data = request.get_json()
    db_type = data.get("db_type")

    if db_type == "postgresql":
        credentials = app.config["POSTGRESQL_CONFIG"].copy()
        schema_name = credentials.get("schema", None)
    elif db_type == "servicenow":
        credentials = app.config["SERVICENOW_CONFIG"].copy()
    elif db_type == "sqlite":
        credentials = {"db_type": "sqlite", "db_path": DATABASE_PATH}
    else:
        return jsonify({"success": False, "error": "Unsupported database type."})

    # Validate credentials
    if not all(value for key, value in credentials.items() if key != "schema"):
        return jsonify({"success": False, "error": f"Incomplete credentials for {db_type}."})

    # Update global credentials
    current_db_credentials = credentials

    # Try to connect
    try:
        if db_type == "postgresql":
            conn = connect_db(db_type=db_type, credentials=current_db_credentials)
            schema_name = current_db_credentials.get("schema", None)
            new_database_schema_string = get_database_schema(conn, db_type, schema_name)
            conn.close()
            with database_schema_lock:
                database_schema_string = new_database_schema_string
        elif db_type == "sqlite":
            conn = connect_db(db_type=db_type, credentials=current_db_credentials)
            new_database_schema_string = get_database_schema(conn, db_type)
            conn.close()
            with database_schema_lock:
                database_schema_string = new_database_schema_string
        elif db_type == "servicenow":
            # For simplicity, assume connection is always successful
            pass

        with conversation_lock:
            conversation_histories.clear()

        return jsonify({"success": True})
    except Exception as e:
        error_message = f"Failed to connect: {str(e)}"
        return jsonify({"success": False, "error": error_message})


@app.route("/chat", methods=["POST"])
def chat():
    logs = []
    user_input = request.json.get("message").strip()
    database_response = ""
    # Use a fixed conversation ID for simplicity
    conversation_id = "default"

    # Determine the system prompt based on the database type
    db_type = current_db_credentials["db_type"]

    if db_type == "postgresql":
        system_prompt_content = """
        You are a helpful assistant for a PostgreSQL database. Whenever any information related to the schema
        or table or column info is asked, just use the schema provided to you.
        If you want tables for a given schema, use queries like this:
        SELECT tablename
            FROM pg_catalog.pg_tables
            WHERE schemaname = {schema_name}
            ORDER BY tablename;
        If column names are asked, this is how the query should look:
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = {tablename}
            AND table_schema = {schema_name}
        - Answer questions by executing SELECT queries using the `execute_sql_function`.
        - If a query execution results in an error, use the `debug_sql_query` function to debug and correct the query.
        - After correcting the query, try executing it again using the `execute_sql_function`.
        """
    elif db_type == "servicenow":
        api_base_url = current_db_credentials["host"]
        api_endpoint = "/api/now/table/problem"  # Default endpoint

        system_prompt_content = f"""
        You are a helpful assistant for querying the ServiceNow API.
        The base API URL is: {api_base_url}
        The default API endpoint is: {api_endpoint}
        When constructing API calls, use this base URL and endpoint, and only specify the necessary query parameters.

        Answer user questions by making appropriate API calls using the `execute_api_call` function.
        In the `execute_api_call` function, you only need to specify the 'params' argument with the appropriate
        'sysparm_query' to fulfill the user's request.

        For example, to get information on a problem ticket with number 'PRB000107560',
        you would call `execute_api_call` with:

        params: {{'sysparm_query': 'number=PRB000107560'}}

        Do not include the base API URL or endpoint in the function call; they are already configured.

        Use 'sysparm_query' to specify query parameters.

        Ensure that the parameters you provide are correct for the user's request.

        Provide the user with the relevant information extracted from the API response.

        Note: Do not include any confidential information in your responses.
        """
    else:
        system_prompt_content = """
        You are a helpful assistant for a SQLite database.
        Answer questions by executing SELECT queries using the `execute_sql_function`.
        """

    # Initialize conversation history with the appropriate system prompt
    with conversation_lock:
        if conversation_id not in conversation_histories:
            system_prompt = {"role": "system", "content": system_prompt_content}
            conversation_histories[conversation_id] = [system_prompt]

    # Retrieve conversation history
    messages = conversation_histories[conversation_id].copy()
    messages.append({"role": "user", "content": user_input})

    # Get the current database schema from the global variable
    with database_schema_lock:
        current_database_schema_string = database_schema_string

    # Define the function specifications for OpenAI
    if db_type == "postgresql" or db_type == "sqlite":
        functions = [
            {
                "type": "function",
                "function": {
                    "name": "execute_sql_function",
                    "description": "Use this function to answer user questions by executing SQL queries.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": f"""
                                SQL query that extracts the information to answer the user's question.
                                SQL should be written using this database schema:
                                {current_database_schema_string}
                                The SQL query should be correct and not modify the database.
                                """,
                            }
                        },
                        "required": ["query"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "debug_sql_query",
                    "description": "Use this function to fix SQL queries that resulted in errors.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The original SQL query that failed.",
                            },
                            "error_message": {
                                "type": "string",
                                "description": "The error message returned when the query was executed.",
                            },
                        },
                        "required": ["query", "error_message"],
                    },
                },
            },
        ]
    elif db_type == "servicenow":
        functions = [
            {
                "type": "function",
                "function": {
                    "name": "execute_api_call",
                    "description": (
                        "Use this function to answer user questions by making API calls to ServiceNow."
                        "Come up with sysparam_query for the query asked to make an api call."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "params": {
                                "type": "object",
                                "description": (
                                    "Query parameters to include in the "
                                    "request, e.g., {'sysparm_query': "
                                    "'number=PRB000107560'}."
                                ),
                            }
                        },
                        "required": ["params"],
                    },
                },
            },
        ]

    assistant_reply = ""
    status_updates = []
    # Loop to handle multiple function calls
    while True:
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                tools=functions,
                tool_choice="auto",
            )
        except openai.APIError as e:
            logging.error(f"OpenAI API error: {e}")
            return jsonify({"error": "An error occurred while communicating with the AI assistant."})

        # Get the assistant's response
        response_message = response.choices[0].message
        messages.append(response_message)
        logs.append(f"Assistant response: {response_message}")

        # Check if the assistant wants to call a function
        if response_message.tool_calls:
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                logging.info(f"Function call - Name: {function_name}, Arguments: {function_args}")
                logs.append(f"Function call - Name: {function_name}, Arguments: {function_args}")

                # Add status update with function name
                status_updates.append(f"Running {function_name}")

                # Handle function calls
                if function_name in function_mappings:
                    # Pass only required arguments
                    function_response = function_mappings[function_name](**function_args, db_type=db_type)
                    function_response_str = str(function_response)  # Ensure it's a string
                    database_response = function_response_str
                    print(f"Function response: {function_response_str}")
                    # Add a 'tool' message with the correct 'tool_call_id'
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": function_response_str,
                        }
                    )
                    logs.append(f"Function response: {function_response_str}")
                else:
                    assistant_reply = "I'm sorry, I cannot perform the requested action."
                    # database_response= ''
                    messages.append({"role": "assistant", "content": assistant_reply})
                    break
            # Continue the loop to let the assistant process the function responses
            continue
        else:
            # Assistant has provided a final answer
            assistant_reply = response_message.content
            if not response_message.tool_calls:
                status_updates.append("Generating final response")
            # database_response = ''
            messages.append({"role": "assistant", "content": assistant_reply})
            break  # Exit the loop

    # Update the conversation history
    with conversation_lock:
        conversation_histories[conversation_id] = messages

    return jsonify(
        {
            "message": assistant_reply,
            "logs": logs,
            "database_response": database_response,
            "status_updates": status_updates,
        }
    )


if __name__ == "__main__":
    app.run(debug=True)
