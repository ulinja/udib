#!/usr/bin/env python3
"""Main entry point for the interactive udib CLI tool."""

from pathlib import Path
from sys import exit
from tempfile import TemporaryDirectory

from cli.clibella import Printer
from cli.parser import get_argument_parser
from core.utils import assert_system_dependencies_installed, download_and_verify_debian_iso
from iso.injection import inject_preseed_file_into_iso
from net.download import download_file
from net.scrape import get_debian_preseed_file_urls, get_debian_iso_urls


def main():

    # check for dependencies
    assert_system_dependencies_installed()
    # create a CLI printer
    p = Printer()
    # create an argument parser and read arguments
    parser = get_argument_parser()
    args = parser.parse_args()

    # parse and verify output file if sepcified
    if args.path_to_output_file:
        path_to_output_file = Path(args.path_to_output_file)
        if "~" in str(path_to_output_file):
            path_to_output_file = path_to_output_file.expanduser()
        path_to_output_file = path_to_output_file.resolve()

        if path_to_output_file.exists():
            p.error(f"Output file already exists: '{path_to_output_file}'.")
            exit(1)
    else:
        path_to_output_file = None

    # parse and verify output dir if sepcified
    if args.path_to_output_dir:
        path_to_output_dir = Path(args.path_to_output_dir)
        if "~" in str(path_to_output_dir):
            path_to_output_dir = path_to_output_dir.expanduser()
        path_to_output_dir = path_to_output_dir.resolve()

        if not path_to_output_dir.is_dir():
            p.error(f"No such directory: '{path_to_output_dir}'.")
            exit(1)
    else:
        path_to_output_dir = None

    if args.subparser_name == "get":
        if args.WHAT == "preseed-file-basic":
            # download the basic example preseedfile

            if not path_to_output_file:
                output_file_name = get_debian_preseed_file_urls()["basic"]["name"]
                if path_to_output_dir:
                    path_to_output_file = path_to_output_dir / output_file_name
                else:
                    path_to_output_file = Path.cwd() / output_file_name

            p.info("Retrieving basic preseed example file...")
            download_file(
                path_to_output_file,
                get_debian_preseed_file_urls()["basic"]["url"],
                show_progress=False,
                printer=p,
            )
            p.success(
                f"Basic preseed example file was saved to '{path_to_output_file}'."
            )
            exit(0)

        elif args.WHAT == "preseed-file-full":
            # download the full example preseedfile

            if not path_to_output_file:
                output_file_name = get_debian_preseed_file_urls()["full"]["name"]
                if path_to_output_dir:
                    path_to_output_file = path_to_output_dir / output_file_name
                else:
                    path_to_output_file = Path.cwd() / output_file_name

            p.info("Retrieving full preseed example file...")
            download_file(
                path_to_output_file,
                get_debian_preseed_file_urls()["full"]["url"],
                show_progress=False,
                printer=p,
            )
            p.success(
                f"Full preseed example file was saved to '{path_to_output_file}'."
            )
            exit(0)

        elif args.WHAT == "iso":
            # download and verify installation image
            p.info("Downloading latest Debian stable x86-64 netinst ISO...")

            if not path_to_output_file:
                output_file_name = get_debian_iso_urls()["image_file"]["name"]
                if path_to_output_dir:
                    path_to_output_file = path_to_output_dir / output_file_name
                else:
                    path_to_output_file = Path.cwd() / output_file_name

            download_and_verify_debian_iso(path_to_output_file, printer=p)
            p.success(f"Debian ISO saved to '{path_to_output_file}'.")
            exit(0)

    elif args.subparser_name == "inject":
        image_file_name = Path(get_debian_iso_urls()["image_file"]["name"])
        if not path_to_output_file:
            output_file_name = image_file_name.stem + "-preseeded" + image_file_name.suffix
            if path_to_output_dir:
                path_to_output_file = path_to_output_dir / output_file_name
            else:
                path_to_output_file = Path.cwd() / output_file_name

        # verify preseed file path
        path_to_preseed_file = Path(args.PRESEEDFILE)
        if "~" in str(path_to_preseed_file):
            path_to_preseed_file = Path(path_to_preseed_file).expanduser()
        path_to_preseed_file = Path(path_to_preseed_file).resolve()
        if not path_to_preseed_file.is_file():
            p.error(f"No such file: '{path_to_preseed_file}'.")
            exit(1)

        # verify image file path if set by user or download fresh iso if unset
        temp_iso_dir = None
        if args.path_to_image_file:
            path_to_image_file = Path(args.path_to_image_file)
            if "~" in str(path_to_image_file):
                path_to_image_file = Path(path_to_image_file).expanduser()
            path_to_image_file = Path(path_to_image_file).resolve()
            if not path_to_image_file.is_file():
                p.error(f"No such file: '{path_to_image_file}'.")
                exit(1)
        else:
            # download a Debian ISO to a temporary directory
            p.info("Downloading the latest Debian x86-64 netinst image...")
            temp_iso_dir = TemporaryDirectory()
            path_to_iso_dir = Path(temp_iso_dir.name)
            path_to_image_file = path_to_iso_dir/image_file_name
            download_and_verify_debian_iso(path_to_image_file, printer=p)

        # inject the preseed file
        inject_preseed_file_into_iso(
            path_to_output_file,
            path_to_image_file,
            path_to_preseed_file,
            printer=p,
        )

        # clear out temporary directory if one was created earlier
        if temp_iso_dir:
            temp_iso_dir.cleanup()

        exit(0)

if __name__ == '__main__':
    main()
