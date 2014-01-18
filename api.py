from collections import namedtuple, defaultdict, deque
import json

import requests
import lxml.html

# When debug is on, no requests are sent to ordbogen.com.
DEBUG = True

LOGIN_URL = 'http://ordbogen.com/ajax/login.json.php'
LOGOUT_URL = 'http://www.ordbogen.com/user/logout.php'
LOOKUP_URL = 'http://www.ordbogen.com/opslag.php?word={word}&dict={lang}'

""" List of valid languages.
These are used by ordbogen.com and are abbreviated by the first two letters
of each language, written in Danish.
"""
VALID_LANGUAGES = ('auto', 'daen', 'daty', 'dafr', 'dapo', 'dait')

""" Session to hold session keys.
Should probably set a user agent string.
"""
session = requests.Session()

TRANSLATED_WORD = namedtuple('TranslatedWord', ['word', 'language', 'wordclass', 'inflection', 'examples'])
WORD_EXAMPLES = namedtuple('WordExamples', ['category', 'example', 'explanation', 'word', 'combination'])


def login(username, password):
    """ Authenticate with ordbogen.com.
    Update global variable `session` with session keys.

    Return bool indicating status and string with error messages.

    """
    # TODO: Check whether we are already logged in or not.
    # This can't really be done until I try and save cookies locally.

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
    langdoc = resultdiv[0].cssselect('h5')[0]

    # This is an ugly hack to create a list of that holds the language once per translation found.
    # If two words were found, this could be [Danish-English, Danish-English].
    languages = deque()
    language = langdoc.text_content()
    while langdoc is not None:
        if langdoc.tag == 'h5':
            language = langdoc.text_content()
        languages.append(language)
        langdoc = langdoc.getnext()
    results = defaultdict(list)
    # Find language translation direction (e.g. Danish->English).
    # Get translations from each language.
    for worddoc in resultdiv[0].cssselect('div.articlePadding'):
        language = languages.popleft()
        word = TRANSLATED_WORD(language=language,
                               word=_getattribute(worddoc, 'input', 'value'),
                               inflection=_gettext(worddoc, 'span.inflection'),
                               wordclass=_gettext(worddoc, 'span.wordclass'),
                               # comment=_gettext(worddoc, 'div.gramComment'),
                               examples=[])
        # Get usage-examples for each word.
        for exampledoc in worddoc.cssselect('div.examples li.articleHover'):
            example = WORD_EXAMPLES(category=_gettext(exampledoc, 'span.category'),
                                    example=_gettext(exampledoc, 'span.example'),
                                    explanation=_gettext(exampledoc, 'span.explanation'),
                                    combination=_gettext(exampledoc, 'span.combination'),
                                    word=_getattribute(exampledoc, 'input.wordBox', 'value'))
            word.examples.append(example)
        results[language].append(word)
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


def _savecookie():
    """ Save the login-cookie from ordbogen.com

    """
    raise NotImplemented()


def _loadcookie():
    """ Load the login-cookie for ordbogen.com

    """
    raise NotImplemented()


def availablelanguages():
    """ Return a list of available languages.
    Languages available depend on the subscription the user has.

    """
    raise NotImplemented()
