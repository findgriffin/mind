#! /usr/bin/env python3
from mind import cli
import sys

if __name__ == "__main__":
    for line in cli.main(sys.argv[1:]):
        print(line)
