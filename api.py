from collections import defaultdict
import json

import requests
import lxml.html

DEBUG = True

LOGIN_URL = 'http://ordbogen.com/ajax/login.json.php'
LOGOUT_URL = 'http://www.ordbogen.com/user/logout.php'
LOOKUP_URL = 'http://www.ordbogen.com/opslag.php?word={word}&dict={lang}'

""" List of valid languages.
These are abbreviated by the first two letters of a language, in Danish.
"""
VALID_LANGUAGES = ('auto', 'daen', 'daty', 'dafr', 'dapo', 'dait')

""" Session to hold session keys. We should probably set a user agent string.
"""
session = requests.Session()


def login(username, password):
    """ Authenticate with ordbogen.com.
    Update global variable `session` with session keys.

    Return bool status and string error.

    """
    # Create payload for jsonrpc.
    payload = {
        "params": [username, password, True, 1],
        "method": "login",
        "id": 'jsonrpc'
    }
    # Send request to server.
    if DEBUG:
        jsonresponse = {'result': {'status': True, 'message': 'Alrighty!'}}
    else:
        r = session.post(LOGIN_URL, data=json.dumps(payload))
        jsonresponse = json.loads(r.text)
    return jsonresponse['result'].get('status', False), jsonresponse['result'].get('message', None)


def lookup(word, lang='auto'):
    """ Look up a word.
    Return type is subject to change.

    """
    if not lang in VALID_LANGUAGES:
        return "Invalid language '{l}'."
    # Perform lookup.
    if DEBUG:
        html = None
        with file('html/{w}.html'.format(w=word), 'r') as f:
            html = f.read()
    else:
        r = session.get(LOOKUP_URL.format(word=word, lang=lang))
        html = r.text
    return _parselookup(html)


def _gettext(doc, selector, num=0):
    """ Get text contents of lxml tree element.

    """
    lst = doc.cssselect(selector)
    if num < len(lst):
        return lst[num].text_content()
    return None


def _getattribute(doc, selector, attribute, num=0):
    """ Get an attribute from lxml tree element.

    """
    lst = doc.cssselect(selector)
    if num < len(lst):
        return lst[num].get(attribute, None)
    return None


def _parselookup(html):
    """ Parse HTML from a lookup request.
    Return type is subject to change.

    """
    doc = lxml.html.fromstring(html)
    resultdiv = doc.cssselect('div.searchArticleResult')
    results = defaultdict(dict)
    # Parse html in to a dict of translations.
    for languagedoc in resultdiv[0].cssselect('h5'):
        # Find language.
        language = languagedoc.text_content()
        results[language] = defaultdict(dict)
        # Get translations from each language.
        for worddoc in languagedoc.getnext():  # worddocs are siblings of language elements.
            word = _getattribute(worddoc, 'input', 'value')
            wordclass = _gettext(worddoc, 'span.wordclass')
            inflection = _gettext(worddoc, 'span.inflection')
            results[language][word]['wordclass'] = wordclass
            results[language][word]['inflection'] = inflection
            # Get examples for each word.
            results[language][word]['examples'] = []
            for exampledoc in worddoc.cssselect('div.examples li.articleHover'):
                example = {'category': _gettext(exampledoc, 'span.category'),
                           'example': _gettext(exampledoc, 'span.example'),
                           'explanation': _gettext(exampledoc, 'span.explanation'),
                           'word': _getattribute(exampledoc, 'input.wordBox', 'value')}
                results[language][word]['examples'].append(example)
    return results


def keepalive():
    """ Tell ordbogen.com that we want to keep connection alive.
    Not sure whether this is needed or not.

    """
    # http://www.ordbogen.com/user/keepalive.php?time=1389915302.2
    raise NotImplemented()


def logout():
    """ Tell ordbogen.com that we want to log out.

    """
    if DEBUG:
        return
    session.get(LOGOUT_URL)
