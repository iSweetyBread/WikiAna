import psycopg2
from configparser import ConfigParser

def load_config(filename = "backend/database_module/database.ini", section = "postgresql"):    
    parser = ConfigParser()
    parser.read(filename)
    
    config = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            config[param[0]] = param[1]
    else:
        raise Exception('Section {0} not found in the {1} file'.format(section, filename))
    
    return config

def connect(config):
    try:
        with psycopg2.connect(**config) as conn:
            print('Connected to the PostgreSQL server')
            return conn
    except (psycopg2.DatabaseError, Exception) as error:
        print(f"Error: {error}")

conn = connect(load_config())
conn.autocommit = True
cursor = conn.cursor()

sql = '''SELECT * FROM employees;'''

cursor.execute(sql)
results = cursor.fetchall()
print(results)

conn.commit()
conn.close()