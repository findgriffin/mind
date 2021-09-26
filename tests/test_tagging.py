import unittest

from mind import mind


class TestTagging(unittest.TestCase):

    def test_extract_no_tags(self):
        # Given
        raw = "one two three"
        # When
        output, tags = mind.extract_tags(raw)
        # Then
        self.assertEqual(output, raw)
        self.assertSetEqual(tags, set())

    def test_extract_a_tag(self):
        # Given
        raw = "one two #three"
        # When
        output, tags = mind.extract_tags(raw)
        # Then
        self.assertEqual(output, "one two")
        set
        self.assertSetEqual(tags, {"three"})

    def test_extract_multiple_tags(self):
        # Given
        raw = "one #two #three"
        # When
        output, tags = mind.extract_tags(raw)
        # Then
        self.assertEqual(output, "one")
        self.assertSetEqual(tags, {"two", "three"})

    def test_extract_duplicated_tag(self):
        # Given
        raw = "one #three two #three"
        # When
        output, tags = mind.extract_tags(raw)
        # Then
        self.assertEqual(output, "one two")
        self.assertSetEqual(tags, {"three"})

    def test_extract_invalid_tags(self):
        # Given
        raw = "# Some heading or another# with#Stuff"
        # When
        output, tags = mind.extract_tags(raw)
        # Then
        self.assertEqual(output, raw)
        self.assertSetEqual(tags, set())

    def test_other_whitespace_gets_replaced(self):
        # Given
        raw = "# Heading\nNext line\t* Indented"
        # When
        output, tags = mind.extract_tags(raw)
        # Then
        self.assertEqual(output, "# Heading Next line * Indented")
        self.assertSetEqual(tags, set())
