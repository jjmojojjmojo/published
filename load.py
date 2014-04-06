"""
Script to set up fake data in the redis database.
"""

import redis

def create(connection, redis_key, **kwargs):
    """
    Create a single file entry.
    
    Keyword arguments will override the corresponding key in the database.
    """
    
    default = {
        'state': 'unpublished',
        'public_uri': "http://gtk-dev2:8080/public.png",
        'private_uri': "http://127.0.0.1:9090/private.png",
    }
    
    model = {}
    
    model.update(default)
    model.update(kwargs)
    
    for key, val in model.iteritems():
        connection.hset(redis_key, key, val)
        
def delete(connection, redis_key):
    """
    Delete a single file entry
    """
    connection.delete(redis_key)
    
    
if __name__ == '__main__':
    connection = redis.StrictRedis(host='localhost', port=6379, db=0)
    
    create(connection, '/private')
    create(connection, '/published', state="published")
    create(connection, '/error_bad_uri', private_uri="http://127.0.0.1:9090/asdfsdfsdfasdfasdfasdfasd")
    create(connection, '/error_unreachable_host', private_uri="http://wef3ef124f12rr234fr12f12f3213f123f12f312f3wqefwefwef:3292/")
    create(connection, '/private_via_ssl', private_uri="https://127.0.0.1:9090/private.png")
    
