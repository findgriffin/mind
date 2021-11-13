import logging
from argparse import Namespace
from datetime import datetime
from pathlib import Path
from random import choices, randint, random
from string import ascii_letters
from unittest.mock import patch
import os
import io
import tempfile
from contextlib import redirect_stdout
import unittest
from unittest import skip

from mind import mind
from tests import setup_context


class TestPerf(unittest.TestCase):

    def setUp(self):
        tmp = tempfile.NamedTemporaryFile(suffix='.db')
        self.tmp = setup_context(self, tmp)
        self.sesh = setup_context(self, mind.Mind(tmp.name, strict=True))
        self.stdout = setup_context(self, redirect_stdout(io.StringIO()))
        self.input = setup_context(self,
                                   patch("builtins.input", return_value="y"))

    @classmethod
    def word(cls, min=3, max=8, prefix='', suffix=''):
        core = "".join(choices(ascii_letters, k=randint(min, max)))
        return prefix + core + suffix

    @classmethod
    def line(cls, words=7, tags=2):
        parts = [TestPerf.word() * words] + [TestPerf.word(prefix="#") * tags]
        return " ".join(parts)

    def test_add_many_and_list(self):
        # Given
        items = 1000
        page_size = 50
        for i in range(items):
            mind.add_content(self.sesh, content=[TestPerf.line()])
        # When
        start = datetime.now()
        for i in range(200):
            mind.do_list(self.sesh, Namespace(cmd=None, num=page_size,
                                              page=(i % (items/page_size))))
        finish = datetime.now()

        # Then
        self.assertLess((finish - start).seconds, 2)

    def test_add_complex_stuff(self):

        # When
        start = datetime.now()
        init = datetime.now()
        for i in range(100):
            lines = [TestPerf.line(words=randint(12, 16),
                                   tags=0) * randint(40, 100)]
            lines.append(TestPerf.line(words=0, tags=randint(20, 40)))
            mind.add_content(self.sesh, content=lines)
        finish = datetime.now()
        verified = datetime.now()

        # Then init, add 100 complex items, and verify all take <1 sec
        self.assertLess((init - start).seconds, 1)
        self.assertLess((finish - init).seconds, 1)
        self.assertLess((verified - finish).seconds, 1)

    @skip
    def test_big_db(self):
        # Given
        MAX = 10*365*10

        # When
        start = datetime.now()
        for i in range(MAX):
            logging.info(f"Iteration {i}")
            if random() < .7:
                mind.add_content(self.sesh,
                                 content=[TestPerf.line(words=2, tags=1)])
            elif random() < .9 and i > 10:
                mind.do_tick(
                    self.sesh, Namespace(tick=str(randint(1, int(i/2)))))
            elif i > 10:
                id = str(randint(1, int(i/2)))
                mind.do_forget(self.sesh, Namespace(forget=id))
        finish = datetime.now()

        # Then
        db_path = Path(self.tmp.name)

        self.assertLess(os.stat(db_path).st_size / 1024, 6000)
        self.assertLess((finish - start).seconds, 70)
        self.assertFalse(db_path.exists())
