import datetime
import psycopg2.extras as pg
import psycopg2.sql as sql
from connection_pool import get_conn

# Function for caching revision data in bulk
# data -> list of dicts with revision data
def cache_revisions(data):
    rows = [(entry.get('*'), entry.get('comment'), entry.get('contentformat'), entry.get('contentmodel'), entry.get('parentid'), entry.get('revid'), entry.get('size'), entry.get('tags'), entry.get('timestamp'), entry.get('user'), entry.get('userid')) for entry in data]

    with get_conn() as conn, conn.cursor() as cur:
        pg.execute_values(cur, """
            INSERT INTO revisions (article, comment, contentformat, contentmodel, parentid, revid, size, tags, timestamp, user, userid)
            VALUES %s
            ON CONFLICT (revid) DO NOTHING
        """, rows)
    conn.commit()

# Function for caching user data in bulk
# data -> list of dicts with user data
def cache_users(data):
    rows = [(entry.get('userid'), entry.get('name'), pg.Json(entry.get('centralids')), pg.Json(entry.get('attachedlocal')), entry.get('editcount'), entry.get('recentactions'), entry.get('registration'), entry.get('groups'), entry.get('implicitgroups'), entry.get('rights'), pg.Json(entry.get('tempexpired'))) for entry in data]
    update_data = sql.SQL(', ').join(sql.SQL('{} = EXCLUDED.{}').format(sql.Identifier(key), sql.Identifier(key)) for key in data[0].keys() if key != 'userid')
    
    with get_conn() as conn, conn.cursor() as cur:
        pg.execute_values(cur, """
            INSERT INTO users (userid, name, centralids, attachedlocal, editcount, recentactions, registration, groups, implicitgroups, rights, tempexpired)
            VALUES %s
            ON CONFLICT (userid) DO UPDATE SET {}
        """.format(update_data), rows)
    conn.commit()
