"""
Mapping of HTTP response code values to strings
"""

HTTP_RESPONSE_CODES = {
    100:    'CONTINUE',
    101:    'SWITCHING PROTOCOLS',
    200:    'OK',
    201:    'CREATED',
    202:    'ACCEPTED',
    204:    'DELETE OK',
    205:    'RESET CONTENT',
    206:    'PARTIAL CONTENT',
    300:    'MULTIPLE CHOICES',
    301:    'MOVED PERMANENTLY',
    302:    'FOUND',
    303:    'SEE OTHER',
    304:    'NOT MODIFIED',
    305:    'USE PROXY',
    307:    'TEMPORARY REDIRECT',
    400:    'BAD REQUEST',
    401:    'UNAUTHORIZED',
    402:    'PAYMENT REQUIRED',
    403:    'FORBIDDEN',
    404:    'NOT FOUND',
    405:    'METHOD NOT ALLOWED',
    406:    'NOT ACCEPTABLE',
    407:    'PROXY AUTHENTICATION REQUIRED',
    408:    'REQUEST TIMEOUT',
    409:    'CONFLICT',
    410:    'GONE',
    411:    'LENGTH REQIRED',
    412:    'PRECONDITION FAILED',
    413:    'REQUEST ENTITY TOO LARGE',
    414:    'REQUEST URI TOO LONG',
    415:    'UNSUPPORTED MEDIA TYPE',
    416:    'REQUEST RANGE NOT SATISFIABLE',
    417:    'EXPECTATION FAILED',
    422:    'INVALID INPUT',
    500:    'SERVER ERROR',
    501:    'NOT IMPLEMENTED',
    502:    'BAD GATEWAY',
    503:    'SERVICE UNAVAILABLE',
    504:    'GATEWAY TIMEOUT',
    505:    'HTTP VERSION NOT SUPPORTED'
}

def response_code_text(value):
    try:
        value = int(value)
        if value not in HTTP_RESPONSE_CODES:
            raise ValueError
        return HTTP_RESPONSE_CODES[value]
    except ValueError:
        raise ValueError('Invalid response code value %s' % value)

