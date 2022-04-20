#!/usr/bin/env python3

from pathlib import Path
import subprocess

def extract_iso(path_to_output_dir, path_to_input_file):
    """Extracts the input ISO-file into the specified directory using 'bsdtar'.

    Parameters
    ----------
    path_to_output_dir : str or pathlike object
        Path to the directory into which the contents of the archive will be
        extracted.
    path_to_input_file : str or pathlike object
        Path to the file/archive which should be extracted.

    Raises
    ------
    RuntimeError
        Raised if 'bsdtar' is not installed or encountered an error during the
        extraction.
    FileNotFoundError
        Raised if the input file does not exist or is not a file.
    NotADirectoryError
        Raised if the output directory does not exist or is not a directory.

    Example
    -------
        extract_iso("/tmp/isocontents", "/home/myuser/downloads/debian-11.iso")
    """

    path_to_output_dir = Path(path_to_output_dir)
    path_to_input_file = Path(path_to_input_file)

    # check if paths are valid
    if not path_to_output_dir.is_dir():
        raise NotADirectoryError(f"No such directory: '{path_to_output_dir}'.")
    if not path_to_input_file.is_file():
        raise FileNotFoundError(f"No such file: '{path_to_input_file}'.")

    # check if 'bsdtar' is installed
    try:
        subprocess.run(["command", "-v", "bsdtar"], check=True)
    except subprocess.CalledProcessError:
        raise RuntimeError(f"Program not found in $PATH: 'bsdtar'.")

    # extract file to destination
    try:
        subprocess.run(
            [
                "bsdtar",
                "-C",
                str(path_to_output_dir),
                "-xf",
                str(path_to_input_file)
            ],
            check=True
        )
    except subprocess.CalledProcessError:
        raise RuntimeError(
            f"An error occurred while extracting '{path_to_input_file}'."
        )
