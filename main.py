# encoding: utf8
from os import environ
import atexit

from clint.textui import colored, puts, indent

from api import login, lookup, logout
import api

api.DEBUG = False


def main(username=None, password=None):
    if username is None:
        username = environ['ORDBOGEN_COM_USERNAME']
    if password is None:
        password = environ['ORDBOGEN_COM_PASSWORD']

    success, msg = login(username, password)
    if not success:
        puts(msg)
        return

    # Start main loop.
    puts("Ordbogen.com: You are logged in as {u}!".format(u=username))
    puts("You can now begin looking up words.")
    lastresults = []
    i = 1
    while True:
        input_ = raw_input()
        if input_ == "_exit":
            break
        if input_ is None:
            continue
        # Print examples for a given word.
        if lastresults != [] and _isint(input_):
            word = lastresults[int(input_) - 1]
            for example in word.examples:
                _printexample(example)
            continue
        # Use ordbogen.com api to look word up.
        results = lookup(input_)
        # Delete line that user just wrote. For now we just put an empty line.
        puts()
        lastresults = []
        for language in results:
            puts(language)
            with indent(4):
                for word in results[language]:
                    lastresults.append(word)
                    _printword(word, i)
                    i += 1
        puts("\nSearch for a new word, or choose to see a word in more details.")
        i = 1
    # We're done!
    logout()


def _(arg):
    """ Return an empty string if arg is None.

    """

    if arg is None:
        return ''
    return arg


def _printword(word, i):
    txt = "{i}. {word} {class_} {inflection}".format(i=i, word=colored.red(word.word),
                                                     class_=colored.blue(_(word.wordclass)),
                                                     inflection=colored.cyan(_(word.inflection)))
    puts(txt)


def _printexample(example):
    txt = ("-{explanation}{combination} {word} "
           "- {example}".format(explanation=colored.green(_(example.explanation)),
                                combination=colored.cyan(_(example.combination)),
                                word=colored.black(_(example.word)),
                                example=colored.magenta(_(example.example))))
    puts(txt)


def _isint(i):
    try:
        int(i)
        return True
    except ValueError:
        return False

if __name__ == '__main__':
    atexit.register(logout)
    try:
        main()
    except KeyboardInterrupt, EOFError:
        puts("Stopping program!")
