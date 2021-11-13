#! /usr/bin/env python3
from mind import mind
import sys

if __name__ == "__main__":
    for line in mind.main(sys.argv[1:]):
        print(line)
