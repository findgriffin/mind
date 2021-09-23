#! /usr/bin/env python3
import logging

from mind import mind
import sys

if __name__ == "__main__":
    args = mind.setup(sys.argv[1:])
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG,
                            format="%(levelname)s: %(message)s")
        logging.info("Verbose logging enabled.")
    else:
        logging.basicConfig(level=logging.INFO, format="%(message)s")
    print(mind.run(args.name))
