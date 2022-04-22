#!/usr/bin/env python3

"""Main entry point for the interactive udib CLI tool."""

from pathlib import Path
import argparse
import os
import shutil
import subprocess
import sys
import tempfile

import clibella
import modiso
import userinput
import webdownload


p = clibella.Printer()


def _assert_system_dependencies_installed():
    """Asserts that all system dependencies are installed.

    System dependencies are those programs whose names are listed in
    the global 'system_programs_required' variable.

    Raises
    ------
    RuntimeError
        Raised when a required program is not accessible in the system
        $PATH.

    """

    # contains the names of all unix program dependencies which must be
    # installed on the local system and available in the local system's $PATH
    system_programs_required = [
        "bsdtar",
        "chmod",
        "cpio",
        "dd",
        "find",
        "gunzip",
        "gzip",
        "md5sum",
        "xargs",
        "xorriso",
    ]

    for program_name in system_programs_required:
        try:
            subprocess.run(
                ["command", "-v", program_name],
                shell=True,
                check=True)
        except subprocess.CalledProcessError:
            raise RuntimeError(
                f"Program not installed or not in $PATH: "
                f"'{program_name}'.")


def _get_argument_parser():
    """Instantiates and configures an ArgumentParser and returns it.

    Examples
    --------
    parser = _get_argument_parser()
    args = parser.parse_args()

    """

    # FIXME add a group hierarchy
    # FIXME capture ISO filesystem name

    parser = argparse.ArgumentParser()

    # create a group of mutually exclusive arguments
    mutually_exclusive_group = parser.add_mutually_exclusive_group(
        required=True)
    mutually_exclusive_group.add_argument(
        "--get-image",
        help="Download the latest, unmodified Debian image and exit.",
        action="store_true")
    mutually_exclusive_group.add_argument(
        "--get-preseed-file",
        help="Download the latest Debian preseed example file and exit.",
        action="store_true")
    mutually_exclusive_group.add_argument(
        "-p",
        "--existing-preseed-file",
        help="Path to the preseed configuration file to use.",
        action="store")

    # add all other arguments
    parser.add_argument(
        "-o",
        "--output-file",
        help="Path to which the resulting file is written.",
        type=str,
        dest="path_to_output_file",
        action="store")
    parser.add_argument(
        "-i",
        "--existing-image",
        help="Use an existing debian image file, do not download a new one.",
        type=str,
        dest="path_to_existing_image",
        action="store")

    return parser


def main():

    # FIXME capture ISO filesystem name
    iso_filesystem_name = "Debian 11.3.0 UDIB"

    parser = _get_argument_parser()
    args = parser.parse_args()

    # check if all system dependencies are installed
    try:
        _assert_system_dependencies_installed()
    except RuntimeError as e:
        p.error(e)
        sys.exit(1)

    # determine where to output files
    # default to ouputting files to the current directory
    # using their original name if not specified by '-o' argument
    path_to_output_dir = Path.cwd()
    path_to_output_file = None

    # check if path_to_output_file is valid and adjust path_to_output_dir if
    # '-o' was set
    if args.path_to_output_file:
        path_to_output_file = Path(args.path_to_output_file).resolve()

        if path_to_output_file.exists() and not path_to_output_file.is_file():
            p.error(f"Specified output location is not a file: "
                    f"'{path_to_output_file}'.")
            sys.exit(1)

        path_to_output_dir = path_to_output_file.parent

    if args.get_image:
        # download latest image and exit
        with tempfile.TemporaryDirectory() as tmp_dir:
            # save image to a temporary directory
            path_to_image_file = webdownload.debian_obtain_image(
                tmp_dir)

            if path_to_output_file:
                # rename file if '-o' flag was specified
                path_to_image_file = path_to_image_file.rename(
                    path_to_output_file.name)
            else:
                # else determine the intended final path
                path_to_output_file = path_to_output_dir/path_to_image_file.name

            # prompt to confirm file removal if output file already exists
            if path_to_output_file.is_file():
                prompt = f"File '{path_to_output_file}' already exists. " \
                    f"Overwrite it?"
                if userinput.prompt_yes_or_no(prompt, ask_until_valid=True):
                    os.remove(path_to_output_file)
                else:
                    p.failure("Did not obtain a new image file.")
                    sys.exit(1)

            # move file from temporary directory to intended path
            path_to_image_file.rename(path_to_output_file)

        sys.exit(0)

    elif args.get_preseed_file:
        # download latest preseed file and exit
        preseed_file_name = "example-preseed.txt"
        preseed_file_url = "https://www.debian.org/"\
            "releases/stable/" + preseed_file_name

        if not path_to_output_file:
            path_to_output_file = path_to_output_dir/preseed_file_name

        # prompt to confirm file removal if output file already exists
        if path_to_output_file.is_file():
            prompt = f"File '{path_to_output_file}' already exists. " \
                f"Overwrite it?"
            if userinput.prompt_yes_or_no(prompt, ask_until_valid=True):
                os.remove(path_to_output_file)
            else:
                p.failure("Did not obtain a new preseed file.")
                sys.exit(1)

        webdownload.download_file(path_to_output_file, preseed_file_url)

        sys.exit(0)

    else:
        # modify image file using specified preseed file
        path_to_preseed_file = Path(args.existing_preseed_file)
        if not path_to_preseed_file.is_file():
            p.error(f"No such file: '{path_to_preseed_file}'.")
            sys.exit(1)

        if args.path_to_existing_image:
            # user has specified an existing image file
            path_to_image_file = Path(args.path_to_existing_image)
            # sanity check
            if path_to_image_file.suffix not in [".iso", ".img"]:
                p.warning(f"Specified image file does not appear to be an ISO "
                          f"or IMG file: '{path_to_image_file}'!")
                if not userinput.prompt_yes_or_no("Proceed anyways?"):
                    p.failure("Did not create a new image file.")
                    sys.exit(1)
        else:
            # download a fresh image file to a temporary directory
            # remember to delete it later!
            path_to_image_file = webdownload.debian_obtain_image(
                tempfile.mkdtemp())

        # extract image file to a temporary directory
        path_to_extracted_iso_dir = Path(tempfile.mkdtemp())
        p.info("Extracting ISO contents...")
        modiso.extract_iso(
            path_to_extracted_iso_dir,
            path_to_image_file)

        # extract image MBR to a temporary directory
        p.info("Extracting master boot record...")
        path_to_mbr = Path(tempfile.mkdtemp())/"mbr.bin"
        modiso.extract_mbr_from_iso(
            path_to_mbr,
            path_to_image_file)

        # append preseed file to extracted initrd
        p.info("Appending preseed file...")
        modiso.append_file_contents_to_initrd_archive(
            path_to_extracted_iso_dir/"install.amd"/"initrd.gz",
            path_to_preseed_file)

        # regenerate md5sum.txt
        p.info("Regenerating MD5 checksum...")
        modiso.regenerate_iso_md5sums_file(path_to_extracted_iso_dir)

        if not path_to_output_file:
            # use original filename with "-udib" appended before the extension
            path_to_output_file = (path_to_output_dir
                                   / (path_to_image_file.with_suffix("").name
                                      + "-udib"
                                      + path_to_image_file.suffix))

        # check if outputfile already exists
        if path_to_output_file.is_file():
            prompt = f"File '{path_to_output_file}' already exists. " \
                f"Overwrite it?"
            if userinput.prompt_yes_or_no(prompt, ask_until_valid=True):
                os.remove(path_to_output_file)
            else:
                p.failure("Did not create a new ISO file.")
                sys.exit(1)

        # repack ISO file
        p.info("Repacking ISO file...")
        modiso.repack_iso(
            path_to_output_file,
            path_to_mbr,
            path_to_extracted_iso_dir,
            iso_filesystem_name)

        # remove temporary directories
        p.info("Cleaning up...")
        shutil.rmtree(path_to_extracted_iso_dir)
        shutil.rmtree(path_to_mbr.parent)

        p.success(f"Wrote the modified ISO to '{path_to_output_file}'.")


if __name__ == "__main__":
    main()
