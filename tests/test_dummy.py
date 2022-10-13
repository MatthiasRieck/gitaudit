from unittest import TestCase
from gitaudit.dummy import dummy


class TestDummy(TestCase):
    def test_dummy(self):
        dummy()
