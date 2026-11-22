from connection_pool import get_conn

# creates tables for caching database according to the required schema
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
                tags TEXT[],
                "timestamp" TIMESTAMPTZ,
                "user" VARCHAR(255),
                userid INT,
                cached_timestamp TIMESTAMPZ DEFAULT NOW()
            )
        """,
        """
            CREATE TABLE users(
                userid INT PRIMARY KEY,
                "name" VARCHAR(255),
                centralids JSONB,
                attachedlocal JSONB,
                editcount INT,
                recentactions INT,
                registration TIMESTAMPTZ,
                "groups" TEXT[],
                implicitgroups TEXT[],
                rights TEXT[],
                tempexpired JSONB,
                cached_timestamp TIMESTAMPZ DEFAULT NOW()
            )
        """
    )
    
    with get_conn as conn, conn.cursor() as cur:
        for command in commands:
            cur.execute(command)
         
# checks, if there are required caching tables in the database   
def check_tables():
    commands = (
        """SELECT EXISTS(SELECT * FROM information_schema.tables WHERE table_name = \'revisions\')""",
        """SELECT EXISTS(SELECT * FROM information_schema.tables WHERE table_name = \'users\')"""
    )
    
    with get_conn as conn, conn.cursor() as cur:
        for command in commands:
            cur.execute(command)
            if not cur.fetchone()[0]:
                conn.close()
                return False
        
    return True

# initializes the required database for caching data
def init():
    if not check_tables():
        create_tables()
        return 0
    return 1