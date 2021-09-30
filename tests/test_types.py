import unittest

from mind import mind


class TestTypes(unittest.TestCase):

    def test_tag_table(self):
        # When
        cmd = mind.build_create_table_cmd("tags", mind.Tag)
        # Then
        self.assertEqual("CREATE TABLE tags(id INTEGER NOT NULL, "
                         "tag TEXT NOT NULL)", cmd)

    def test_stuff_table(self):
        # When
        cmd = mind.build_create_table_cmd("stuffs", mind.Stuff)
        # Then
        self.assertEqual("CREATE TABLE stuffs(id INTEGER NOT NULL, "
                         "body TEXT NOT NULL, state INTEGER NOT NULL, "
                         "PRIMARY KEY (id))", cmd)
