from argparse import Namespace
from contextlib import redirect_stdout
from io import StringIO
from os import stat
from pathlib import Path
from random import randint, random
from tempfile import NamedTemporaryFile
from timeit import Timer
from unittest import TestCase
from unittest.mock import patch

from mind import mind
from tests import setup_context, line


class TestFsPerf(TestCase):

    def setUp(self):
        tmp = NamedTemporaryFile(suffix='.db')
        self.tmp = setup_context(self, tmp)
        self.sesh = setup_context(self, mind.Mind(tmp.name, strict=True))
        self.stdout = setup_context(self, redirect_stdout(StringIO()))
        self.input = setup_context(self,
                                   patch("builtins.input", return_value="y"))

    def random_id(self) -> int:
        return randint(1, max(int(self.sesh.head().sn/2), 2))

    def do_iteration(self):
        if random() < .7:
            mind.add_content(self.sesh,
                             content=[line(words=2, tags=1)])
        elif random() < .9:
            mind.do_tick(
                self.sesh, Namespace(tick=str(self.random_id())))
        else:
            mind.do_forget(self.sesh, Namespace(forget=str(self.random_id())))

    def test_medium_db(self):
        # Given
        iterations = 10*365
        # When / Then
        self.assertLessEqual(Timer(self.do_iteration).timeit(iterations), 9)
        self.assertLess(stat(Path(self.tmp.name)).st_size / 1024, 500)

    def test_big_db(self):
        # Given
        iterations = 10*365*10
        # When / Then
        self.assertLessEqual(Timer(self.do_iteration).timeit(iterations), 90)
        self.assertLess(stat(Path(self.tmp.name)).st_size / 1024, 5_000)
