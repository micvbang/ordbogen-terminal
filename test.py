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
