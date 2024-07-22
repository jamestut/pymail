import io
import json
import jsonschema
import jsonschema.exceptions
import subprocess

_app_key = None
_sendto = None


def application(environ, start_response):
    assert _app_key
    assert _sendto

    if environ.get("REQUEST_METHOD") != "POST":
        return _do_return(405, [("Allow", "POST")], start_response)

    request_length = environ.get("CONTENT_LENGTH")
    try:
        request_length = int(request_length)
    except (TypeError, ValueError):
        _do_return(400, None, start_response)
        return [b"Unknown request length"]

    input_stream = environ["wsgi.input"]
    try:
        reqbody = json.loads(input_stream.read(request_length))
    except json.JSONDecodeError:
        _do_return(400, None, start_response)
        return [b"Request body is not a valid JSON"]

    try:
        jsonschema.validate(reqbody, _request_schema)
    except jsonschema.exceptions.ValidationError:
        _do_return(400, None, start_response)
        return [b"Malformed request body"]

    if reqbody["key"] != _app_key:
        return _do_return(403, None, start_response)

    mailbody = [
        b"Subject: ",
        _stob(reqbody["subject"]),
        b"\n\n",
        _stob(reqbody["body"]),
    ]
    spr = subprocess.run(
        ["sendmail", _sendto],
        input=b"".join(mailbody),
        stderr=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        check=False,
    )
    if spr.returncode == 1:
        _do_return(500, None, start_response)
        return [b"Request error: ", spr.stderr]

    _do_return(200, None, start_response)
    return [b"Success!"]


def set_app_key(key):
    global _app_key
    _app_key = key


def set_destination(addr):
    global _sendto
    _sendto = addr


_http_ret_codes = {
    200: "OK",
    400: "Bad Request",
    403: "Forbidden",
    405: "Method Not Allowed",
    500: "Internal Server Error",
}

_request_schema = {
    "type": "object",
    "properties": {
        "key": {"type": "string"},
        "subject": {"type": "string"},
        "body": {"type": "string"},
    },
    "required": ["key", "subject", "body"],
}


def _do_return(code, header, start_response):
    assert code in _http_ret_codes
    respmsg = f"{code} {_http_ret_codes[code]}"
    if not header:
        header = []
    start_response(respmsg, header)
    return [_stob(respmsg)]


def _stob(msg: str):
    return msg.encode("utf-8")
