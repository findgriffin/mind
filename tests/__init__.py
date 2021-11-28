from random import choices, randint
from string import ascii_letters


def setup_context(testcase, cm):
    """Use a contextmanager to setUp a test case."""
    val = cm.__enter__()
    testcase.addCleanup(cm.__exit__, None, None, None)
    return val


def word(min=3, max=8, prefix='', suffix=''):
    core = "".join(choices(ascii_letters, k=randint(min, max)))
    return prefix + core + suffix


def line(words=7, tags=2):
    return " ".join([word() * words] + [word(prefix="#") * tags])
