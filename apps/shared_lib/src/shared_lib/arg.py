import argparse
import sys


def get_args(arguments: list[str]) -> dict:
    parser = argparse.ArgumentParser()
    for arg in arguments:
        parser.add_argument(f"--{arg}", required=True)
    return parser.parse_args().__dict__


def get_glue_args(arguments: list[str]) -> dict:
    from awsglue.utils import getResolvedOptions

    return getResolvedOptions(sys.argv, arguments)
