from argparse import Namespace
from contextlib import redirect_stdout
from datetime import datetime
from pathlib import Path
from random import randint, random
from unittest import TestCase
from unittest.mock import patch
import io
import logging
import os
import tempfile

from mind import mind
from tests import setup_context, line


class TestFsPerf(TestCase):

    def setUp(self):
        tmp = tempfile.NamedTemporaryFile(suffix='.db')
        self.tmp = setup_context(self, tmp)
        self.sesh = setup_context(self, mind.Mind(tmp.name, strict=True))
        self.stdout = setup_context(self, redirect_stdout(io.StringIO()))
        self.input = setup_context(self,
                                   patch("builtins.input", return_value="y"))

    def test_big_db(self):
        # Given
        MAX = 10*365*10

        # When
        start = datetime.now()
        for i in range(MAX):
            logging.info(f"Iteration {i}")
            if random() < .7:
                mind.add_content(self.sesh,
                                 content=[line(words=2, tags=1)])
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
        print(f"DB size: {os.stat(db_path).st_size}")
        self.assertLess((finish - start).seconds, 55)
