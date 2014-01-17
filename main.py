from os import environ
import json
import requests

LOGIN_URL = 'http://ordbogen.com/ajax/login.json.php'

LOOKUP_URL = 'http://www.ordbogen.com/opslag.php?word={word}&dict=auto'

# Session that holds session keys.
# Possibly set userAgent string
session = requests.Session()


def main():
    success, error = login(environ['ORDBOGEN_COM_USERNAME'],
                           environ['ORDBOGEN_COM_PASSWORD'])
    if not success:
        print("Could not log in: {e}".format(e=error))
        return
    print("Logged in...")


def login(username, password):
    """ Log in to ordbogen.com.
    Updates `session` with session keys.

    """
    payload = {
        "params": [username, password, True, 1],
        "method": "login",
        "id": 'jsonrpc'
    }

    r = session.post(LOGIN_URL, data=json.dumps(payload))

    # Check that we were actually logged in.
    jsonresponse = json.loads(r.text)
    return jsonresponse['result'].get('status', False), jsonresponse['result'].get('message', None)


def lookup(word):
    """ Look up a word.

    """
    r = session.get(LOOKUP_URL.format(word=word))
    print(r.text.encode('utf8'))


def keepalive():
    # http://www.ordbogen.com/user/keepalive.php?time=1389915302.2
    pass


if __name__ == '__main__':
    main()
