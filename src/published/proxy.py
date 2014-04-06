from webob import Response, Request
from webob import exc

import redis
import pprint
import httplib
from urlparse import urlparse

class Proxy(object):
    """
    Simple remote proxy. 
    
    Inspired by https://bitbucket.org/dahlia/wsgi-proxy
    
    TODO: add authentication
    TODO: test with S3
    TODO: convert to plugin API
    TODO: SSL support
    
    """
    remote = None
    chunk_size = None
    
    def __init__(self, remote, chunk_size=2048):
        """
        TODO: add connection params here for auth, S3 special stuff, etc.
        """
        self.remote = urlparse(remote)
        self.chunk_size = chunk_size
        
    def __call__(self, environ, start_response):
        try:
            if self.remote.scheme == 'https':
                connection = httplib.HTTPSConnection(self.remote.netloc)
            else:
                connection = httplib.HTTPConnection(self.remote.netloc)
            
            connection.request("GET", self.remote.path)
            response = connection.getresponse()
            
            headers = response.getheaders()
            
            start_response('{0.status} {0.reason}'.format(response), headers)
            
            while True:
                chunk = response.read(self.chunk_size)
                if chunk:
                    yield chunk
                else:
                    break
        except Exception, e:
            # TODO: use webob for this?
            # response = exc.HTTPInternalServerError("Error")
            # start_response(response.status, response.headers.items())
            # yield response.body
            
            print "ERROR: %s" % (e,)
            response = exc.HTTPInternalServerError(str(e))
            
            body = "<html><body><h1>Error</h1></body></html>"
             
            headers = [
                ('Content-type', 'text/html'),
            ]
            
            start_response('500 Internal Server Error', headers)
            yield body
            
            
            

class ProxyPublisher(object):
    """
    WSGI application that looks at the request URI.
    
    Communicates with the data store to decide if the requested file is 
    published or not.
    
    Returns a redirect to the "public" server if the requested file is published,
    otherwise returns the file contents themselves, proxied from the remote
    server.
    """
    
    redis = None
    options = None
    
    defaults = {
        'redis_host': '127.0.0.1',
        'redis_port': '6379',
        'redis_db': '0'
    }
    
    def __init__(self, **kwargs):
        """
        Takes a set of keyword arguments:
        
        redis_host = the hostname where the redis server is running
                     defaults to 127.0.0.1
        redis_port = the port number that redis is listening on. Defaults to
                     6379
        redis_db = the database to use. Defaults to 0
        """
        self.options = {}
        self.options.update(self.defaults)
        self.options.update(kwargs)
        
        self.redis = redis.StrictRedis(
            host=self.options['redis_host'], 
            port=self.options['redis_port'], 
            db=self.options['redis_db']
        )
    
    def load(self, key):
        """
        Load the data from the data store
        """
        info = self.redis.hgetall(key)
        
        return info
    
    def __call__(self, environ, start_response):
        """
        Proxies a request to the production server, if the 
        """
        req = Request(environ)
        
        info = self.load(req.path)
        
        if info:
            if info['state'] == 'published':
                res = exc.HTTPMovedPermanently(location=info['public_uri'])
            elif info['state'] == 'unpublished':
                res = Proxy(info['private_uri'])
            else: 
                res = exc.HTTPInternalServerError("Could not determine state of object.")
        else:
            res = exc.HTTPNotFound('Not Found')
        
        return res(environ, start_response)
