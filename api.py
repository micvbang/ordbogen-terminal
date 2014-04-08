# encoding: utf8
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
WORD_SUGGEST_URL = BASE_URL + "/wordcompletion/get_wordsuggestions.php?string={word}&dict={lang}"

""" List of valid languages.
These are used by ordbogen.com and are abbreviated by the first two letters
of each language, written in Danish.
"""
DICTIONARIES = {
    'auto': "Alle ordbøger",
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
    'a001': "Tysk / Dansk / Tysk}"}


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
_dictionarylanguages = []


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
    return jsonresponse['result'].get('status', False), jsonresponse['result'].get('message', None)


def logout():
    """ Tell ordbogen.com that we want to log out.

    """
    session.get(LOGOUT_URL)


def lookup(word, lang='auto'):
    """ Look up a word.
    Return type is subject to change.

    """
    if lang not in DICTIONARIES:
        return "Invalid language '{l}'."
    # Perform lookup.
    r = session.get(LOOKUP_URL.format(word=word, lang=lang))
    html = r.text
    return _parselookup(html)


def wordsuggestions(word, lang='auto'):
    """ Return a list of word suggestions.

    """
    if lang not in DICTIONARIES:
        return "Invalid language '{l}'".format(l=lang)
    r = session.get(WORD_SUGGEST_URL.format(word=word, lang=lang))
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


def languages():
    """ Return a list of available languages.
    Languages available depend on the subscription the user has.

    """
    # If there are no
    if not _dictionarylanguages:
        _parsedictionarylanguages()
    return [DICTIONARIES[lang] for lang in _dictionarylanguages]


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
    global _dictionarylanguages
    if not html:
        html = session.get(BASE_URL).text
    doc = lxml.html.fromstring(html)
    options = doc.cssselect('#dict option')
    _dictionarylanguages = [option.get('value')
                            for option in doc.cssselect("#dict option")]


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


def _gettranslationlanguages(doc):
    lis = doc.cssselect("#dictsmenu li")
    return [li.get('id')[:-5] for li in lis]
