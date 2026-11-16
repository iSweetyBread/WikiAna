import psycopg2
from connect import connect
from config import load_config

# Basic function for adding a row into PostgreSQL database
# table -> string for the name of the table
# db_values -> dict, where keys are column names and values are their respective values
async def add_entry(table, db_values):
    keys = ""
    values = ""
    for i in db_values:
        keys += i + ', '
        values += db_values[i] + ', '
    keys = keys[:-2]
    values = values[:-2]
    
    command = f"""INSERT INTO {table} ({keys}) VALUES ({values});"""
    
    try:
        conn = connect(load_config())
        conn.autocommit = True
    
        with conn.cursor() as cur:
            cur.execute(command)
    except (psycopg2.DatabaseError, Exception) as error:
        print(f"database_init.py error: {error}")
        
# Basic function for deleting a row from PostgreSQL database
# table -> string for the name of the table
# id -> tuple, where [0] is the column name (for primary key id) and [1] is its value
async def remove_entry(table, id):
    command = f"""DELETE FROM {table} WHERE {id[0]} = {id[1]};"""
    
    try:
        conn = connect(load_config())
        conn.autocommit = True
    
        with conn.cursor() as cur:
            cur.execute(command)
    except (psycopg2.DatabaseError, Exception) as error:
        print(f"database_init.py error: {error}")

# Basic function for updating a row from PostgreSQL database
# table -> string for the name of the table
# db_values -> dict, where keys are column names and values are their respective values
# id -> tuple, where [0] is the column name (for primary key id) and [1] is its value
async def update_entry(table, id, db_values):
    command_text = ""
    for i in db_values:
        command_text += i + ' = ' + db_values[i] + ', '
    command_text = command_text[:-2]
        
    command = f"""UPDATE {table} SET {command_text} WHERE {id[0]} = {id[1]};"""
    
    try:
        conn = connect(load_config())
        conn.autocommit = True
    
        with conn.cursor() as cur:
            cur.execute(command)
    except (psycopg2.DatabaseError, Exception) as error:
        print(f"database_init.py error: {error}")