# encoding: utf8
from collections import namedtuple, defaultdict
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
LOOKUP_URL = BASE_URL + '/opslag.php?word={word}&dict={dic}'
WORD_SUGGEST_URL = BASE_URL + "/wordcompletion/get_wordsuggestions.php?string={word}&dict={dic}"

""" List of valid dictionaries.
These are used by ordbogen.com and are abbreviated by the first two letters
of each language, written in Danish.
"""
DICTIONARIES = {
    'auto': "Automatisk",
    'a016': "Arabisk / Dansk / Arabisk",
    'a021': "Blinkenberg & Høybye Fransk / Dansk / Fransk",
    'ddob': "DDO (Den Danske Ordbog)",
    'ddbo': "Den Danske Betydningsordbog",
    'ddgr': "Den Danske Grammatik- og Staveordbog",
    'ddno': "Den Danske Netordbog",
    'ddsv': "Den Danske Skriveordbog",
    'ddsy': "Den Danske Synonymordbog",
    'fred': "Ejendomsordbog Fransk-Dansk",
    'a000': "Engelsk / Dansk / Engelsk",
    'a050': "Engelsk / Kinesisk / Engelsk",
    'a002': "Fransk / Dansk / Fransk",
    'ddbs': "Hvad er det nu, det hedder?",
    'a008': "Italiensk / Dansk / Italiensk",
    'musk': "Musikordbogen",
    'a017': "Norsk / Engelsk / Norsk",
    'fvdd': "Ordbogen over faste vendinger",
    'a102': "Politikens Engelskordbog",
    'a100': "Politikens Franskordbog",
    'pfre': "Politikens Fremmedordbog",
    'a103': "Politikens Første Engelskordbog",
    'plda': "Politikens Lille Danskordbog",
    'pndo': "Politikens Nudansk Ordbog",
    'prbo': "Politikens Retskrivnings- og Betydningsordbog",
    'pret': "Politikens Retskrivningsordbog",
    'prim': "Politikens Rimordbog",
    'psko': "Politikens Skoleordbog",
    'a104': "Politikens Store Engelskordbog",
    'psyn': "Politikens Synonymordbog",
    'a101': "Politikens Tyskordbog",
    'a006': "Portugisisk / Dansk / Portugisisk",
    'rtsk': "Retskrivningsordbogen",
    'a005': "Spansk / Dansk / Spansk",
    'a004': "Svensk / Dansk / Svensk",
    'a001': "Tysk / Dansk / Tysk"}


""" Tuples to store scraped translations in. """
TranslatedWord = namedtuple('TranslatedWord', ['word', 'language', 'wordclass',
                                               'inflection', 'details'])
WordDetails = namedtuple('WordDetails', ['category', 'example', 'explanation',
                                         'word', 'combination'])
WordSuggestion = namedtuple('WordSuggestion', ['word', 'language'])


""" Session to hold session keys.
Should probably set a user agent string.
"""
session = requests.Session()

""" Dictionaries user has subscribed to. """
_availabledictionaries = []


def login(username, password):
    """ Authenticate with ordbogen.com.
    Update global variable `session` with session keys.

    Return bool indicating status and string with error messages.

    """
    if _loggedin(username):
        return True, 'OK'
    # Create payload for jsonrpc.
    payload = {
        "params": [username, password, True, 1],
        "method": "login",
        "id": 'jsonrpc'
    }
    r = session.post(LOGIN_URL, data=json.dumps(payload))
    jsonresponse = json.loads(r.text)
    _savecookies()
    return (jsonresponse['result'].get('status', False),
            jsonresponse['result'].get('message', None))


def logout():
    """ Tell ordbogen.com that we want to log out.

    """
    session.get(LOGOUT_URL)


def lookup(word, dic='auto'):
    """ Look up a word.
    Return type is subject to change.

    """
    if dic not in DICTIONARIES:
        print "Invalid dictionary '{d}'.".format(d=dic)
        return []
    # Perform lookup.
    r = session.get(LOOKUP_URL.format(word=word, dic=dic))
    html = r.text
    doc = lxml.html.fromstring(html)
    # Get list of dictionaries that have results.
    # dicts = _dictionarieswithhits(doc)
    return _parselookup(doc)


def wordsuggestions(word, dic='auto'):
    """ Return a list of word suggestions.

    """
    if dic not in DICTIONARIES:
        return "Invalid dictionary '{l}'".format(l=dic)
    r = session.get(WORD_SUGGEST_URL.format(word=word, dic=dic))
    res = []
    for d in r.json():
        res.append(WordSuggestion(d['word'], d['shortdict']))
    return res


def keepalive():
    """ Tell ordbogen.com that we want to keep connection alive.
    Not sure whether this is needed or not.

    """
    # http://www.ordbogen.com/user/keepalive.php?time=1389915302.2
    raise NotImplemented()


def availabledictionaries():
    """ Return a list of available dictionaries.
    The dictionaries available depend on the subscription the user has.

    """
    return {lang: DICTIONARIES[lang] for lang in _availabledictionaries}


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


def _loggedin(username):
    """ Load saved cookies and check if we're already logged in.

    """
    _loadcookies()
    response = session.get(BASE_URL)
    loggedin = username in response.text
    if loggedin:
        _parsedictionarylanguages(response.text)
    return loggedin


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


def _parsedictionarylanguages(html=None):
    global _availabledictionaries
    if not html:
        html = session.get(BASE_URL).text
    doc = lxml.html.fromstring(html)
    options = doc.cssselect('#dict option')
    _availabledictionaries = [option.get('value') for option in options]


def _parselookup(doc):
    """ Parse HTML from a lookup request.
    Return type is subject to change.

    """
    resultdiv = doc.cssselect('div.searchArticleResult')[0]
    langdoc = resultdiv.cssselect('h5')[0]

    # This is an ugly hack to create a list of that holds the language once per translation found.
    # If two words were found, this could be [Danish-English, Danish-English].
    language = langdoc.text_content()
    results = defaultdict(list)
    # Find language translation direction (e.g. Danish->English).
    # Get translations from each language.
    for worddoc in resultdiv[0].cssselect('div.articlePadding'):
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


def _dictionarieswithhits(doc):
    """ Get a list of the dictionaries that had hits on a query.

    """
    lis = doc.cssselect("#dictsmenu li")
    return [li.get('id')[:-5] for li in lis]
