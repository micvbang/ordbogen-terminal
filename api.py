from collections import namedtuple, defaultdict, deque
from os.path import dirname, join, abspath, exists as pathexists
import json

import requests
import lxml.html


here = lambda *args: join(abspath(dirname(__file__)), *args)

# File in which login-cookies are stored.
COOKIE_FILE = here('cookies')

# URLs used
BASE_URL = 'http://ordbogen.com/'
LOGIN_URL = BASE_URL + '/ajax/login.json.php'
LOGOUT_URL = BASE_URL + '/user/logout.php'
LOOKUP_URL = BASE_URL + '/opslag.php?word={word}&dict={lang}'

""" List of valid languages.
These are used by ordbogen.com and are abbreviated by the first two letters
of each language, written in Danish.
"""
VALID_LANGUAGES = ('auto',  # Automatically choose a dictionary
                   'daen',  # Danish-English
                   'enda',  # English-Danish
                   'daty',  # Danish-German
                   'dafr',  # Danish-French
                   'dait',  # Danish-Italian
                   'pret',  # Politikens retskrivningsordbog
                   'pndo',  # Politikens nudansk ordbog
                   'fred',  # French-Danish ejendomsordbog
                   )

""" Session to hold session keys.
Should probably set a user agent string.
"""
session = requests.Session()

TranslatedWord = namedtuple('TranslatedWord', ['word', 'language', 'wordclass',
                                               'inflection', 'details'])
WordDetails = namedtuple('WordDetails', ['category', 'example', 'explanation',
                                         'word', 'combination'])


def login(username, password):
    """ Authenticate with ordbogen.com.
    Update global variable `session` with session keys.

    Return bool indicating status and string with error messages.

    """
    # TODO: Check whether we are already logged in or not.
    # This can't really be done until I try and save cookies locally.

    if _loggedin(username):
        print("Logged in using cookies from last visit.")
        return True, 'OK'
    # Create payload for jsonrpc.
    payload = {
        "params": [username, password, True, 1],
        "method": "login",
        "id": 'jsonrpc'
    }
    # Send request to server.
    r = session.post(LOGIN_URL, data=json.dumps(payload))
    jsonresponse = json.loads(r.text)
    _savecookies()
    return jsonresponse['result'].get('status', False), jsonresponse['result'].get('message', None)


def _loggedin(username):
    """ Load saved cookies and check if we're already logged in.

    """
    _loadcookies()
    response = session.get(BASE_URL)
    return username in response.text


def lookup(word, lang='auto'):
    """ Look up a word.
    Return type is subject to change.

    """
    if not lang in VALID_LANGUAGES:
        return "Invalid language '{l}'."
    # Perform lookup.
    r = session.get(LOOKUP_URL.format(word=word, lang=lang))
    html = r.text
    return _parselookup(html)


def _gettext(doc, selector, num=0):
    """ Get text contents of lxml tree element.

    """
    lst = doc.cssselect(selector)
    if num < len(lst):
        return lst[num].text_content().strip()
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
        word = TranslatedWord(language=language,
                              word=_getattribute(worddoc, 'input', 'value'),
                              inflection=_gettext(worddoc, 'span.inflection'),
                              wordclass=_gettext(worddoc, 'span.wordclass'),
                              # comment=_gettext(worddoc, 'div.gramComment'),
                              details=[])
        # Get usage-details for each word.
        for detaildoc in worddoc.cssselect('div.examples li.articleHover'):
            detail = WordDetails(category=_gettext(detaildoc, 'span.category'),
                                 example=_gettext(detaildoc, 'span.example'),
                                 explanation=_gettext(detaildoc, 'span.explanation'),
                                 combination=_gettext(detaildoc, 'span.combination'),
                                 word=_getattribute(detaildoc, 'input.wordBox', 'value'))
            word.details.append(detail)
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
    session.get(LOGOUT_URL)


def _savecookies():
    """ Save the cookies from `session` to COOKIE_FILE

    """
    with file(COOKIE_FILE, 'w+') as f:
        cookiedict = session.cookies.get_dict()
        f.write(json.dumps(cookiedict))


def _loadcookies():
    """ Load cookies from COOKIE_FILE in to `session`.

    """
    if not pathexists(COOKIE_FILE):
        return
    with file(COOKIE_FILE, 'r') as f:
        cookiedict = json.loads(f.read())
        session.cookies = requests.cookies.cookiejar_from_dict(cookiedict)


def availablelanguages():
    """ Return a list of available languages.
    Languages available depend on the subscription the user has.

    """
    raise NotImplemented()
