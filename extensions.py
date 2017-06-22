import os

from datetime import datetime
from enum import Enum
from urllib.parse import urlparse, unquote, parse_qs


DEFAULT_PAGE = 'index.html'
RESPONSE_STATUS = {
    200: "200 OK",
    403: "403 Forbidden",
    404: "404 Not Found",
    405: "405 Method Not Allowed",
}

TYPES = {
    'css': 'text/css',
    'gif': 'image/gif',
    'html': 'text/html',
    'js': 'application/javascript',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'png': 'image/png',
    'swf': 'application/x-shockwave-flash'
}

HTTP_VERSION = '1.1'
SERVER_NAME = 'name'
HTTP_DATE_FORMAT = '%a, %d %b %Y %H:%M:%S GMT'

def http_format_date_now(format):
    return datetime.utcnow().strftime(format)

class ResponseCode(Enum):
    OK = 200
    FORBIDDEN = 403
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405


class Handler:
    def __init__(self, request, root_dir):
        self.request = request
        self.root_dir = root_dir

    def handle(self):
        if self.request.method in ["GET", "HEAD"]:
            response = self.__handle()
        else:
            response = Response(ResponseCode.METHOD_NOT_ALLOWED)
        return response

    def __handle(self):
        real_path = os.path.normpath(self.root_dir + '/' + self.request.path)
        response = Response(code=ResponseCode.NOT_FOUND)

        if os.path.commonprefix([real_path, self.root_dir]) != self.root_dir:
            return response

        if os.path.isfile(os.path.join(real_path, DEFAULT_PAGE)):
            real_path = os.path.join(real_path, DEFAULT_PAGE)
        elif os.path.exists(os.path.join(real_path)):
            response.code = ResponseCode.FORBIDDEN
        try:
            with open(real_path, 'rb') as fd:
                content = fd.read()
                response.body = content if self.request.method == 'GET' else b''
                response.content_length = len(content)
                response.content_type = self.__get_content_type(real_path)
                response.code = ResponseCode.OK
        except IOError:
            pass

        return response

    def __get_content_type(self, path):
        file_type = path.split('.')[-1]
        return TYPES.get(file_type, '')

    def __get_content_length(self, path):
        with open(path, 'rb') as fd:
            return len(fd.read())


class Request:
    def __init__(self, raw_request):
        self.method = raw_request.split(b' ')[0].decode()
        self.headers = self.__extract_headers(raw_request)
        self.host = self.headers.get('Host', '')
        self.url, self.path, self.query_params = self.__parse_url(raw_request)
        self.data = raw_request.split(b'\r\n\r\n')[1]

    def __parse_url(self, raw_request):
        raw_url = self.host + raw_request.split(b' ')[1].decode()
        if '://' not in raw_url:
            raw_url = '//' + raw_url
        parsed_url = urlparse(raw_url)
        return parsed_url.geturl(), unquote(parsed_url.path), parse_qs(unquote(parsed_url.query))

    def __extract_headers(self, raw_request):
        headers = raw_request.split(b'\r\n\r\n')[0]
        headers = headers.split(b'\r\n')[1:]
        headers_dict = {}
        for header in headers:
            header = header.decode().split(': ')
            headers_dict.update({header[0]: header[1]})
        return headers_dict

    def __extract_query(self):
        query = ''
        temp_list = self.url.split('?', 1)
        if len(temp_list) > 1:
            query = temp_list[1]
        return query

    def __extract_query_params(self):
        query_params = {}
        parameters_list = self.query.split('&')
        for param in parameters_list:
            param = param.split('=')
            values_set = query_params.get(param[0], set())
            values_set.add(param[1])
            query_params.update({param[0]: values_set})
        return query_params


class Response:
    def __init__(self, code, content_length=0, content_type='', content=b''):
        self.code = code
        self.content_length = content_length
        self.content_type = content_type
        self.body = content

    def build(self):
        if self.code is ResponseCode.OK:
            response = self.__response_ok()
        else:
            response = self.__response_bad()
        return response

    def __response_ok(self):
        return ('HTTP/{http_version} {http_status}\r\n'
                'Server: {server_name}\r\n'
                'Date: {date}\r\n'
                'Connection: Close\r\n'
                'Content-Length: {content_length}\r\n'
                'Content-Type: {content_type}\r\n\r\n').format(http_version=HTTP_VERSION,
                                                               http_status=RESPONSE_STATUS[self.code.value],
                                                               server_name=SERVER_NAME,
                                                               date=http_format_date_now(HTTP_DATE_FORMAT),
                                                               content_length=self.content_length,
                                                               content_type=self.content_type).encode() + self.body

    def __response_bad(self):
        return ('HTTP/{http_version} {http_status}\r\n'
                'Server: {server_name}\r\n'
                'Date: {date}\r\n'
                'Connection: Closed\r\n\r\n').format(http_version=HTTP_VERSION,
                                                     http_status=RESPONSE_STATUS[self.code.value],
                                                     server_name=SERVER_NAME,
                                                     date=http_format_date_now(HTTP_DATE_FORMAT)).encode()

