import logging
from argparse import Namespace
from datetime import datetime
from pathlib import Path
from random import choices, randint, random
from string import ascii_letters, ascii_lowercase, digits
import os
import unittest
from unittest import skip

from mind import mind


def word():
    return "".join(choices(ascii_letters, k=randint(3, 8)))


class TestPerf(unittest.TestCase):

    def test_add_many_and_list(self):
        # Given
        random_chars = "".join(choices(ascii_lowercase, k=11))
        db_path = Path(f"/tmp/testrun-{random_chars}.db").expanduser()
        items = 1000
        page_size = 50
        with mind.Mind(db_path, strict=True) as sesh:
            for i in range(items):
                letters = choices(ascii_letters, k=11)
                tag = choices(digits, k=4)
                mind.add_content(sesh, content=[f"{letters} #{tag}"])
            # When
            start = datetime.now()
            for i in range(200):
                mind.do_list(sesh, Namespace(cmd=None, num=page_size,
                                             page=(i % (items/page_size))))
        finish = datetime.now()
        os.remove(db_path)

        # Then
        self.assertLess((finish - start).seconds, 2)
        self.assertFalse(db_path.exists())

    def test_add_complex_stuff(self):
        # Given
        random_chars = "".join(choices(ascii_lowercase, k=11))
        db_path = Path(f"/tmp/testrun-{random_chars}.db").expanduser()

        # When
        start = datetime.now()
        with mind.Mind(db_path, strict=True) as sesh:
            init = datetime.now()
            for i in range(100):
                lines = [" ".join(
                    [word()] * randint(12, 16))] * randint(40, 100)
                lines.append(" #".join([word()]) * randint(20, 40))
                mind.add_content(sesh, content=lines)
            finish = datetime.now()
        verified = datetime.now()
        # File size: os.stat(db_name).st_size / 1024)
        os.remove(db_path)

        # Then init, add 100 complex items, and verify all take <1 sec
        self.assertLess((init - start).seconds, 1)
        self.assertLess((finish - init).seconds, 1)
        self.assertLess((verified - finish).seconds, 1)
        self.assertFalse(db_path.exists())

    @skip
    def test_big_db(self):
        # Given
        random_chars = "".join(choices(ascii_lowercase, k=11))
        db_path = Path(f"/tmp/testrun-{random_chars}.db").expanduser()
        MAX = 10*365*10

        # When
        start = datetime.now()
        with mind.Mind(db_path, strict=True) as sesh:
            for i in range(MAX):
                logging.info(f"Iteration {i}")
                if random() < .7:
                    letters = choices(ascii_letters, k=11)
                    tag = choices(digits, k=4)
                    mind.add_content(sesh, content=[f"{letters} #{tag}"])
                elif random() < .9 and i > 10:
                    mind.do_tick(
                        sesh, Namespace(tick=[str(randint(1, int(i/2)))]))
                elif i > 10:
                    mind.do_forget(
                        sesh, Namespace(forget=[str(randint(1, int(i/2)))]))
        finish = datetime.now()

        # Then

        self.assertLess(os.stat(db_path).st_size / 1024, 5000)
        os.remove(db_path)
        self.assertLess((finish - start).seconds, 70)
        self.assertFalse(db_path.exists())
