from os import environ
import unittest
import lxml.html
from os.path import join, abspath, dirname

from api import (wordsuggestions, languages, lookup, keepalive, login,
                 _gettranslationlanguages)
from main import _isint

here = lambda *args: join(abspath(dirname(__file__)), *args)


class TestAPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        username = environ['ORDBOGEN_COM_USERNAME']
        password = environ['ORDBOGEN_COM_PASSWORD']
        # login(username=username, password=password)

    def test_wordsuggestions(self):
        pass
        # wordsuggestions('kat')

    def test_gettranslationlanguages(self):
        file_ = here('html/hold.html')
        doc = None
        with open(file_, 'r') as f:
            doc = lxml.html.fromstring(f.read())

        langs = ['daen', 'daty', 'pret', 'pndo']
        self.assertTrue(_gettranslationlanguages(doc) == langs)


class TestMain(unittest.TestCase):

    def test_isint(self):
        # Can be converted to int
        self.assertTrue(_isint(1))
        self.assertTrue(_isint(1, 2, 3))
        self.assertTrue(_isint('1'))
        self.assertTrue(_isint('1', '2', '3'))

        # Can not be converted to int.
        self.assertFalse(_isint([1]))
        self.assertFalse(_isint((1,)))


if __name__ == '__main__':
    unittest.main()
