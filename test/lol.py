from unittest import TestCase
from hurricane_electric import AutonomousSystemNumber
from json import dumps

class AutonomousSystemNumberTest(TestCase):

    def test_toJson(self):
         print AutonomousSystemNumber('a', 'b', 0, 1).toJSON()


