from os import environ
import unittest

from api import (wordsuggestions, availablelanguages, lookup, keepalive, login)


class TestAPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        username = environ['ORDBOGEN_COM_USERNAME']
        password = environ['ORDBOGEN_COM_PASSWORD']
        login(username=username, password=password)

    def test_wordsuggestions(self):
        print(wordsuggestions('kat'))


if __name__ == '__main__':
    unittest.main()
