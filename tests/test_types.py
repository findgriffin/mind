import unittest

from mind import mind


class TestTypes(unittest.TestCase):

    def test_tag_table(self):
        # When
        cmd = mind.create_cmd2("tags", mind.Tag)
        # Then
        self.assertEqual("CREATE TABLE tags(id INTEGER NOT NULL, "
                         "tag TEXT NOT NULL)", cmd)

    def test_stuff_table(self):
        # When
        cmd = mind.create_cmd2("stuffs", mind.Stuff)
        # Then
        self.assertEqual("CREATE TABLE stuffs(id TEXT NOT NULL, "
                         "body TEXT NOT NULL, state INTEGER NOT NULL)", cmd)
