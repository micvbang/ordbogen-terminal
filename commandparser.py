import re


class Command(object):
    EXIT = 1
    LIST_DICTS = 2
    SET_DICT = 3
    LOOKUP = 4
    DETAILS = 5
    HELP = 6


def parse(txt):
    if txt == ".exit":
        return Command.EXIT, None
    elif txt == ".dicts":
        return Command.LIST_DICTS, None
    elif txt in (".?", ".help"):
        return Command.HELP
    elif re.match("_dict=\w{4}", txt):
        return Command.SET_DICT, txt[6:]
    elif _isint(txt):
        return Command.DETAILS, int(txt)
    else:
        return Command.LOOKUP, txt


def _isint(*args):
    """ Return true if all args are or can be converted to integers.

    """
    try:
        return all(map(lambda arg: int(arg), args))
    except (TypeError, ValueError):
        return False
