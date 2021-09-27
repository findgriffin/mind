from argparse import Namespace
from datetime import datetime
from random import choices, randint
from string import ascii_letters, ascii_lowercase, digits
import os
import unittest

from mind import mind


def word():
    return "".join(choices(ascii_letters, k=randint(3, 8)))


class TestPerf(unittest.TestCase):

    def test_add_many_and_list(self):
        # Given
        random_chars = "".join(choices(ascii_lowercase, k=11))
        db_name = f"/tmp/testrun-{random_chars}.db"
        with mind.get_db(db_name) as con:
            for i in range(1000):
                letters = choices(ascii_letters, k=11)
                tag = choices(digits, k=4)
                mind.do_add_2(con, content=[f"{letters} #{tag}"])

        # When
        start = datetime.now()
        for i in range(200):
            with mind.get_db(db_name) as con:
                mind.do_list(con, Namespace(cmd=None))
        finish = datetime.now()
        os.remove(db_name)

        # Then
        self.assertLess((finish - start).seconds, 2)

    def test_add_complex_stuff(self):
        # Given
        random_chars = "".join(choices(ascii_lowercase, k=11))
        db_name = f"/tmp/testrun-{random_chars}.db"

        # When
        start = datetime.now()
        with mind.get_db(db_name) as con:
            for i in range(200):
                lines = [" ".join(
                    [word()] * randint(12, 16))] * randint(40, 100)
                lines.append(" #".join([word()]) * randint(10, 15))
                mind.do_add_2(con, content=lines)
        finish = datetime.now()
        # File size: os.stat(db_name).st_size / 1024)
        os.remove(db_name)

        # Then
        self.assertLess((finish - start).seconds, 1)