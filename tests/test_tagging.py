import unittest

from mind import mind


class TestTagging(unittest.TestCase):

    def test_tag_set(self):
        # Given
        tags = [mind.Tag(1, "one"), mind.Tag(1, "two")]
        # When
        output = mind.canonical_tags(tags)
        # Then
        self.assertEqual("Tags [one, two]", output)

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

    def test_valid_tags(self):
        self.assertEqual("1", mind.is_tag("#1"))
        self.assertEqual("1333tc0d3", mind.is_tag("#1333tc0d3"))
        self.assertEqual("hello", mind.is_tag("#hEllo"))

    def test_not_tags(self):
        self.assertFalse(mind.is_tag("##"))
        self.assertFalse(mind.is_tag("#wut is"))
        self.assertFalse(mind.is_tag("#wut "))
        self.assertFalse(mind.is_tag("#w!t"))
        self.assertFalse(mind.is_tag("#surprise!"))
        self.assertFalse(mind.is_tag("#foo\n"))
        self.assertFalse(mind.is_tag("#"))
