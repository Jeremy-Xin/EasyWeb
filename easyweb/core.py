# WSGI server and WSGI handler
class BaseServer:
    def __init__(self, host, port, **kargs):
        self.host = host
        self.port = port
        self.options = kargs

    def run(self):
        raise NotImplementedError


class WSGIServer(BaseServer):
    def run(self, handler):
        from wsgiref.simple_server import make_server

        server = make_server(self.host, self.port, handler)
        server.serve_forever()


def run(server=WSGIServer, host='', port=8000, **kargs):
    if isinstance(server, type) and issubclass(server, BaseServer):
        server = server(host, port, **kargs)
    else:
        raise RuntimeError('Server must be a class of BaseServer')

    print('listening {} on {}...'.format(host, port))
    try:
        server.run(WSGIHandler)
    except KeyboardInterrupt:
        pass


def WSGIHandler(environ, start_response):
    # start_response('200 OK', [('Content-Type', 'text/html')])
    global request
    global response
    request.initialize(environ)
    response.initialize()
    # print(request._environ)
    try:
        handler, params = Router.match_url(request.path, request.method)
        if handler:
            output = handler(**params)
        else:
            response.status = 404
            output = 'Page not found'
    except Exception as e:
        response.status = getattr(e, 'http_status', 500)
        output = b'Internal server error'
    status = '{} {}'.format(response.status, HTTP_CODES[response.status])
    start_response(status, [('Content-Type', 'text/html')])
    output = to_bytes(output)
    return [output]


def to_bytes(bytes_or_str):
    if isinstance(bytes_or_str, str):
        value = bytes_or_str.encode('utf-8')
    else:
        value = bytes_or_str
    return value # Instance of bytes


simple_route_mapping = {}
regex_route_mapping = {}

import re
# router
class Router:
    def __init__(self):
        pass

    def route(cls, url, **kwargs):
        def wrapper(handler):
            cls.add_route(url, handler)

        return wrapper

    @classmethod
    def add_route(cls, url, handler, method='GET'):
        method = method.strip().upper()
        if re.match(r'^(\w+/)*\w*$', url):
            simple_route_mapping.setdefault(method, {})[url] = handler
        else:
            url = cls.compile_route(url)
            regex_route_mapping.setdefault(method, []).append([url, handler])

    @classmethod
    def compile_route(cls, route):
        route = re.sub(r':([a-zA-Z_]+)(?P<uniq>[^\w/])(?P<re>.+?)(?P=uniq)', r'(?P<\1>\g<re>)', route)
        route = re.sub(r':([a-zA-Z_]+)', r'(?P<\1>[^/]+)', route)
        return re.compile('^%s$' % route)

    @classmethod
    def match_url(cls, url, method='GET'):
        url = url.strip()
        handler = simple_route_mapping.get(method, {}).get(url, None)
        if handler:
            return (handler, {})

        routes = regex_route_mapping.get(method, [])
        for i in range(len(routes)):
            match = routes[i][0].match(url)
            if match:
                handler = routes[i][1]
                if i > 0:
                    routes[i - 1], routes[i] = routes[i], routes[i - 1]
                return (handler, match.groupdict())
        return (None, None)

route = Router().route


class Request:
    def initialize(self, environ):
        self._environ = environ
        self.path = self._environ.get('PATH_INFO', '/').strip()
        self.method = self._environ.get('REQUEST_METHOD', 'GET').upper()

class Response:
    def initialize(self):
        self.status = 200
        self.content_type = 'text/html'
        self.header = {}

request = Request()
response = Response()


from jinja2 import Environment, FileSystemLoader
from jinja2 import Template as jinja2_Template


class BaseTemplate(object):
    def __init__(self):
        raise NotImplementedError

    def load(self):
        raise NotImplementedError

    def render(self):
        raise NotImplementedError


TEMPLATE_DIRS = 'templates'


class Template(BaseTemplate):
    def __init__(self, template=None):
        self.env = Environment(loader=FileSystemLoader(TEMPLATE_DIRS))
        if template:
            self.tmpl = jinja2_Template(template)

    def load(self, template_name):
        try:
            self.tmpl = self.env.get_template(template_name)
        except BaseException as e:
            raise Exception('template error')

    def render(self, *args, **kwargs):
        return str(self.tmpl.render(*args, **kwargs))


def render_template(template_name, *args, **kwargs):
    try:
        tmpl = Template()
        tmpl.load(template_name)
        return tmpl.render(*args, **kwargs)
    except BaseException as e:
        raise Exception('template error')



HTTP_CODES = {
    100: 'CONTINUE',
    101: 'SWITCHING PROTOCOLS',
    200: 'OK',
    201: 'CREATED',
    202: 'ACCEPTED',
    203: 'NON-AUTHORITATIVE INFORMATION',
    204: 'NO CONTENT',
    205: 'RESET CONTENT',
    206: 'PARTIAL CONTENT',
    300: 'MULTIPLE CHOICES',
    301: 'MOVED PERMANENTLY',
    302: 'FOUND',
    303: 'SEE OTHER',
    304: 'NOT MODIFIED',
    305: 'USE PROXY',
    306: 'RESERVED',
    307: 'TEMPORARY REDIRECT',
    400: 'BAD REQUEST',
    401: 'UNAUTHORIZED',
    402: 'PAYMENT REQUIRED',
    403: 'FORBIDDEN',
    404: 'NOT FOUND',
    405: 'METHOD NOT ALLOWED',
    406: 'NOT ACCEPTABLE',
    407: 'PROXY AUTHENTICATION REQUIRED',
    408: 'REQUEST TIMEOUT',
    409: 'CONFLICT',
    410: 'GONE',
    411: 'LENGTH REQUIRED',
    412: 'PRECONDITION FAILED',
    413: 'REQUEST ENTITY TOO LARGE',
    414: 'REQUEST-URI TOO LONG',
    415: 'UNSUPPORTED MEDIA TYPE',
    416: 'REQUESTED RANGE NOT SATISFIABLE',
    417: 'EXPECTATION FAILED',
    500: 'INTERNAL SERVER ERROR',
    501: 'NOT IMPLEMENTED',
    502: 'BAD GATEWAY',
    503: 'SERVICE UNAVAILABLE',
    504: 'GATEWAY TIMEOUT',
    505: 'HTTP VERSION NOT SUPPORTED',
}
