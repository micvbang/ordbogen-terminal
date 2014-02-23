from os import environ
import unittest

from api import (wordsuggestions, availablelanguages, lookup, keepalive, login)
from main import _isint


class TestAPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        username = environ['ORDBOGEN_COM_USERNAME']
        password = environ['ORDBOGEN_COM_PASSWORD']
        login(username=username, password=password)

    def test_wordsuggestions(self):
        print(wordsuggestions('kat'))


class TestMain(unittest.TestCase):

    def test_isint(self):
        # Ints are ints.
        self.assertTrue(_isint(1, 2, 3, 4, 5, 6, 7, 8, 9))
        self.assertTrue(_isint(1))

        # Strings, lists, and tuples are not ints.
        self.assertFalse(_isint('1'))
        self.assertFalse(_isint([1]))
        self.assertFalse(_isint((1,)))


if __name__ == '__main__':
    unittest.main()
