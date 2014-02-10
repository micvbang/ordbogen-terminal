#!/usr/bin/python
# encoding: utf8
from os import environ
from sys import argv

from clint.textui import colored, puts, indent

from api import login, lookup
import api

api.DEBUG = False


def interactive(word=None, username=None, password=None):
    """ Log in to ordbogen.com and start an interactive shell.
    """
    if username is None:
        username = environ['ORDBOGEN_COM_USERNAME']
    if password is None:
        password = environ['ORDBOGEN_COM_PASSWORD']

    success, msg = login(username, password)
    if not success:
        puts(msg)
        return

    # Start interactive loop.
    puts("Ordbogen.com: You are logged in as {u}!".format(u=username))
    _prompt()
    words = None
    if word:
        words = _lookup_and_print(word)
    while True:
        input_ = raw_input()
        if input_ == "_exit_":
            return
        # Check if user wants see a detailed translation
        if _isint(input_, words):
            _printdetailed(input_, words)
        # User wants to look up word.
        else:
            words = _lookup_and_print(input_)
        _prompt()


def _lookup_and_print(input_):
    """ Look up word and print found translations.
    Number each translation so that it can be referenced by the user.

    Return a list of `WordDetails` for each translation. Translations are
    numbered (as described above) 1-indexed, so the 'real' index in to the list
    is i - 1.

    """
    # Use ordbogen.com api to look word up.
    results = lookup(input_)
    # Delete line that user just wrote. For now we just put an empty line.
    puts()
    words = []
    for language in results:
        # Print language 'header'.
        puts(language)
        with indent(4):
            for word in results[language]:
                words.append(word)
                _printword(word, "%i. " % len(words))
    return words


def _prompt():
    puts("\nSearch for a word or view a translation in details.")
    puts("Search: ", newline=False)


def _(arg):
    """ Return an empty string if arg is None, else return arg.

    """

    return arg if arg is not None else ''


def _printword(word, indicator=None):
    """ Pretty print an instance of `TranslatedWord` from api.py

    `indicator` must be None or a string, and will be printed just
    before `word`.

    """
    # Abusing automatic string concatenation.
    txt = ("{indicator}{word} {class_} {inflection}"
           "".format(indicator=_(indicator), word=colored.red(word.word),
                     class_=colored.blue(_(word.wordclass)),
                     inflection=colored.cyan(_(word.inflection))))
    puts(txt)


def _printdetailed(input_, words):
    """ Pretty print detailed translation from an instance of TranslatedWord.

    """
    index = int(input_) - 1
    if index < 0 or index >= len(words):
        puts("You must choose a number in the range 1-" + str(len(words) + 1))
        return
    word = words[index]
    # Print header
    puts()
    puts(word.language)
    # Print details
    with indent(4):
        _printword(word)
        for detail in word.details:
            _printdetail(detail)


def _printdetail(detail):
    """ Pretty print an instance of `WordDetails` from api.py

    """
    txt = ("-{explanation}{combination} {word} - {example}"
           "".format(explanation=colored.green(_(detail.explanation)),
                     combination=colored.cyan(_(detail.combination)),
                     word=colored.black(_(detail.word)),
                     example=colored.magenta(_(detail.example))))
    puts(txt)


def _isint(*args):
    """ Return true if all args are integer.

    """
    for arg in args:
        try:
            int(arg)
            return True
        except ValueError:
            return False


if __name__ == '__main__':
    try:
        interactive(" ".join(argv[1:]))
    except (KeyboardInterrupt, EOFError):
        puts("Stopping program!")
