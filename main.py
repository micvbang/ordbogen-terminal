#!/usr/bin/python
# encoding: utf8
from os import environ
import sys

from clint.textui import colored, puts, indent

from api import login, lookup, availabledictionaries
import api

api.DEBUG = False


def main(args):
    """ Log in to ordbogen.com and start an interactive shell.

    """
    username = environ['ORDBOGEN_COM_USERNAME']
    password = environ['ORDBOGEN_COM_PASSWORD']

    success, msg = login(username, password)
    if not success:
        puts(msg)
        return

    puts("Ordbogen.com: You are logged in as {u}!\n".format(u=username))
    _printavailabledictionaries()
    _interactive(word=args)


def _interactive(word=None):
    words = None
    if word:
        words = _lookup_and_print(word)
    _prompt()

    # Main loop.
    while True:
        input_ = raw_input()
        # Check whether a command was given.
        if _parsecommand(input_):
            continue
        # Check if user wants see a detailed translation.
        if _isint(input_):
            _printdetailed(input_, words)
        # User wants to look up word.
        else:
            words = _lookup_and_print(input_)
        _prompt()


def _parsecommand(txt):
    """ Much too simple command parsing

    """
    if txt == "_exit":
        sys.exit(0)
    elif txt == "_dicts":
        _printavailabledictionaries()


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
    # Print detailed information if we only found 1 word.
    if len(words) == 1:
        _printdetailed(1, words)
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
                     word=colored.yellow(_(detail.word)),
                     example=colored.magenta(_(detail.example))))
    puts(txt)


def _isint(*args):
    """ Return true if all args are or can be converted to integers.

    """
    try:
        return all(map(lambda arg: int(arg), args))
    except (TypeError, ValueError):
        return False


def _printavailabledictionaries():
    print("The following availabledictionaries are available:")
    for i, lang in enumerate(availabledictionaries()):
        print "{i}: {l}".format(i=i + 1, l=lang)


if __name__ == '__main__':
    try:
        main(" ".join(sys.argv[1:]))
    except (KeyboardInterrupt, EOFError):
        puts("Stopping program!")
