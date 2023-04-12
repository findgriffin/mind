from mind.app import handle_query
from mind.mind import Mind


def test_empty_query():
    assert handle_query(Mind(), '{}')
