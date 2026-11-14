import psycopg2
from connect import connect
from config import load_config

def create_tables():
    commands = (
        """
            CREATE TABLE revisions (
                article TEXT,
                "comment" TEXT,
                contentformat VARCHAR(255),
                contentmodel VARCHAR(255),
                parentid INT,
                revid INT PRIMARY KEY,
                "size" INT,
                tags TEXT,
                "timestamp" TIMESTAMPTZ,
                "user" VARCHAR(255),
                userid INT,
                cached_timestamp TIMESTAMP
            )
        """,
        """
            CREATE TABLE users(
                userid INT PRIMARY KEY,
                "name" VARCHAR(255),
                centralids JSONB,
                attachedlocal JSONB,
                editcount INT,
                recentreactions INT,
                registration TIMESTAMPTZ,
                "groups" TEXT,
                implicitgroups TEXT,
                rights TEXT,
                tempexpired JSONB,
                cached_timestamp TIMESTAMP
            )
        """,
        """
            ALTER TABLE revisions
            ADD CONSTRAINT fk_revisions_users
            FOREIGN KEY (userid)
            REFERENCES users(userid)
        """
    )
    
    try:
        conn = connect(load_config())
        conn.autocommit = True
        
        with conn.cursor() as cur:
            for command in commands:
                cur.execute(command)
    except (psycopg2.DatabaseError, Exception) as error:
        print(f"database_init.py error: {error}")
        
def check_tables():
    commands = (
        """SELECT EXISTS(SELECT * FROM information_schema.tables WHERE table_name = \'revisions\')""",
        """SELECT EXISTS(SELECT * FROM information_schema.tables WHERE table_name = \'userss\')"""
    )
    
    try:
        conn = connect(load_config())
        conn.autocommit = True
        
        with conn.cursor() as cur:
            for command in commands:
                cur.execute(command)
                if not cur.fetchone()[0]:
                    return False
    except (psycopg2.DatabaseError, Exception) as error:
        print(f"database_init.py error: {error}")
    
    return True
        
def init():
    if not check_tables():
        create_tables()
        return 0
    return 1