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
        with mind.Mind(db_path, strict=True) as sesh:
            for i in range(1000):
                letters = choices(ascii_letters, k=11)
                tag = choices(digits, k=4)
                mind.add_content(sesh, content=[f"{letters} #{tag}"])
            # When
            start = datetime.now()
            for i in range(200):
                mind.do_list(sesh, Namespace(cmd=None, num=50))
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
            for i in range(200):
                lines = [" ".join(
                    [word()] * randint(12, 16))] * randint(40, 100)
                lines.append(" #".join([word()]) * randint(10, 15))
                mind.add_content(sesh, content=lines)
        finish = datetime.now()
        # File size: os.stat(db_name).st_size / 1024)
        os.remove(db_path)

        # Then
        self.assertLess((finish - start).seconds, 1)
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
