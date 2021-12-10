from argparse import Namespace
from contextlib import redirect_stdout
from io import StringIO
from random import choice
from timeit import Timer
from unittest import TestCase
from unittest.mock import patch

from mind.mind import add_content, do_forget, do_tick, Mind
from tests import setup_context


class TestVerifyPerf(TestCase):
    MEM = ":memory:"

    def setUp(self) -> None:
        self.sesh = setup_context(self, Mind(self.MEM, strict=False))
        self.stdout = setup_context(self, redirect_stdout(StringIO()))
        self.input = setup_context(self,
                                   patch("builtins.input", return_value="y"))

    def test_verify_many(self):
        for i in range(1000):
            add_content(self.sesh, [f"hello{i} #tag{i} #tagtwo{i} #t{i}"])
            if choice((True, False)):
                do_forget(self.sesh, Namespace(forget=str(i)))
            else:
                do_tick(self.sesh, Namespace(tick=str(i)))

        self.assertLessEqual(Timer(self.sesh.verify).timeit(10), 3)
