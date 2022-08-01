"""Commandline argument parsing utilities."""

from argparse import ArgumentParser


def get_argument_parser():
    """Sets up an argparse ArgumentParser and returns it."""

    mainparser = ArgumentParser(
        description="Debian ISO preseeding tool.",
    )

    # add mutually exclusive optional arguments to top-level parser
    mainparser_group = mainparser.add_mutually_exclusive_group()
    mainparser_group.add_argument(
        "-o",
        "--output-file",
        action='store',
        type=str,
        dest='path_to_output_file',
        metavar='OUTPUTFILE',
        help="File as which the retrieved/generated file will be saved",
    )
    mainparser_group.add_argument(
        "-O",
        "--output-dir",
        action='store',
        type=str,
        dest='path_to_output_dir',
        metavar='OUTPUTDIR',
        help="Directory into which the retrieved/generated file will be written",
    )

    # register subparsers for the 'get' and 'inject' subcommands
    subparsers = mainparser.add_subparsers(
        required=True,
        title="Subcommands",
        description="A choice of actions you want udib to take",
        help="You must specify one of these",
        dest="subparser_name",
    )
    subparser_get = subparsers.add_parser(
        "get",
        description="Retrieve an unmodified Debian ISO or example preseed file",
    )
    subparser_inject = subparsers.add_parser(
        "inject",
        description="Inject a preseed file into a Debian ISO",
    )

    # register arguments for the 'get' subcommand
    subparser_get.add_argument(
        "WHAT",
        choices=['preseed-file-basic', 'preseed-file-full', 'iso'],
        action='store',
        type=str,
        metavar='WHAT',
        help="The type of file you want UDIB to retrieve. "
             "Valid options are: 'preseed-file-basic', 'preseed-file-full' "
             "or 'iso'.",
    )

    # register arguments for the 'inject' subcommand
    subparser_inject.add_argument(
        "PRESEEDFILE",
        action='store',
        type=str,
        metavar='PRESEEDFILE',
        help="Path to the preseed file you want to inject",
    )
    subparser_inject.add_argument(
        "-i",
        "--image-file",
        action='store',
        type=str,
        dest='path_to_image_file',
        metavar='IMAGEFILE',
        help="Path to the ISO you want to modify",
    )

    return mainparser
