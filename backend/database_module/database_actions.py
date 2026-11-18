from psycopg2 import sql
from connection_pool import get_conn

# Basic function for adding a row into PostgreSQL database
# table -> string for the name of the table
# db_values -> dict, where keys are column names and values are their respective values
# conflict_column -> string for column name, where values may be identical to already cached value
# used for handling re-caching (primarily for re-caching users)
def add_entry(table, db_values, conflict_column = None):
    if conflict_column:
        conflict_action = sql.SQL("ON CONFLICT ({conflict_column}) DO UPDATE SET {update_data}").format(
            update_data = sql.SQL(', ').join(sql.SQL('{} = EXCLUDED.{}').format(sql.Identifier(key), sql.Identifier(key)) for key in db_values.keys() if key != conflict_column)
        )
    else:
        conflict_action = sql.SQL("")
    
    query = sql.SQL("INSERT INTO {table} ({cols}) VALUES ({placeholders}) {conflict_action}").format(
        table = sql.Identifier(table),
        cols = sql.SQL(', ').join(map(sql.Identifier, db_values.keys())),
        placeholders = sql.SQL(', ').join(sql.Placeholder() * len(db_values)),
        conflict_action = conflict_action
    )
    
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(query, list(db_values.values()))
        conn.close()
        
# Basic function for deleting a row from PostgreSQL database
# table -> string for the name of the table
# id -> tuple, where [0] is the column name (for primary key id) and [1] is its value
def remove_entry(table, id):
    query = sql.SQL("DELETE FROM {table} WHERE {id_table} = {id_value}").format(
        table = sql.Identifier(table),
        id_table = sql.Identifier(id[0]),
        id_value = sql.Placeholder()
    )
    
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(query, (id[1],))

# Basic function for updating a row from PostgreSQL database
# table -> string for the name of the table
# db_values -> dict, where keys are column names and values are their respective values
# id -> tuple, where [0] is the column name (for primary key id) and [1] is its value
def update_entry(table, id, db_values):
    query = sql.SQL("UPDATE {table} SET {placeholders} WHERE {id_table} = {id_value}").format(
        table = sql.Identifier(table),
        id_table = sql.Identifier(id[0]),
        id_value = sql.Placeholder(),
        placeholders = sql.SQL(', ').join(sql.SQL('{} = {}').format(sql.Identifier(key), sql.Placeholder()) for key in db_values.keys())
    )
    
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(query, list(db_values.values()) + [id[1]])