import os
import random
import string
import unittest
from datetime import datetime

from mind import mind


class TestPerf(unittest.TestCase):

    def test_add_many_and_list(self):
        # Given
        bits = random.choices(string.ascii_lowercase, k=11)
        db_name = f"/tmp/testrun-{bits}.db"
        with mind.get_db(db_name) as con:
            for i in range(1000):
                letters = random.choices(string.ascii_letters, k=11)
                tag = random.choices(string.digits, k=4)
                mind.do_add(con, content=f"{letters} #{tag}")

        # When
        start = datetime.now()
        for i in range(1000):
            with mind.get_db(db_name) as con:
                mind.do_list(con)
        finish = datetime.now()
        os.remove(db_name)

        # Then
        self.assertLess((finish - start).seconds, 2)
