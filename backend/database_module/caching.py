from database_actions import add_entry
import datetime
import psycopg2.extras as pg

async def cache_revisions(data):
    for entry in data:
        data_dict = {
            'article': entry['*'],
            'comment': entry['comment'],
            'contentformat': entry['contentformat'],
            'contentmodel': entry['contentmodel'],
            'parentid': entry['parentid'],
            'revid': entry['revid'],
            'size': entry['size'],
            'tags': ', '.join(entry['tags']),
            'timestamp': entry['timestamp'],
            'user': entry['user'],
            'userid': entry['userid'],
            'cached_timestamp': datetime.datetime.now().isoformat()
        }
        
        await add_entry('revisions', data_dict)
        
async def cache_users(data):
    for entry in data:
        data_dict = {
            'userid': entry['userid'],
            'name': entry['name'],
            'centralids': pg.Json(entry['centralids']),
            'attachedlocal': pg.Json(entry['attachedlocal']),
            'edicount': entry['edicount'],
            'recentactions': entry['recentactions'],
            'registration': entry['registration'],
            'groups': ', '.join(entry['groups']),
            'implicitgroups': ', '.join(entry['implicitgroups']),
            'rights': ', '.join(entry['rights']),
            'tempexpired': pg.Json(entry['tempexpired']),
            'cached_timestamp': datetime.datetime.now().isoformat()
        }
    
        await add_entry('users', data_dict)