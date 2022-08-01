"""A collection of general utilities, not specific to any module."""

from crypt import crypt, METHOD_SHA512
from getpass import getpass
from os import remove, rename
from pathlib import Path
from subprocess import run, STDOUT, PIPE
from sys import exit
from tempfile import TemporaryDirectory

from cli.clibella import Printer
from core.exceptions import MissingDependencyError
from gpg.exceptions import VerificationFailedError
from gpg.keystore import debian_signing_key_is_imported, import_debian_signing_key
from gpg.verify import assert_detached_signature_is_valid
from net.download import download_file
from net.scrape import get_debian_iso_urls


def hash_user_password(printer=None):
    """Prompts for a password and prints the resulting hash.

    The resulting hash can be added to the preseed file to set a user password:
    d-i passwd/root-password-crypted PASSWORDHASH
    """

    if printer is None:
        p = Printer()
    else:
        if not isinstance(printer, Printer):
            raise TypeError(f"Expected a {type(Printer)} object.")

    password = getpass("Enter a password: ")
    password_confirmed = getpass("Enter the password again: ")
    if not password_confirmed == password:
        p.failure("Passwords did not match")
        return

    p.info("Password hash:")
    p.info(crypt(password, crypt.METHOD_SHA512))

def assert_system_dependencies_installed():
    """Checks whether all system dependencies required by udib are installed.

    The programs used by udib must be accessible within the system's PATH
    environment variable.

    Raises
    ------
    MissingDependencyError
        If a required dependency is not installed.
    """

    _REQUIRED_PROGRAMS = [
        "xorriso", "gpg", "cpio", "sha512sum",
    ]

    for program in _REQUIRED_PROGRAMS:
        try:
            run(["command", "-v", program], shell=True, check=True)
        except subprocess.CalledProcessError:
            raise MissingDependencyError(
                f"Program not installed or not in $PATH: "
                f"'{program}'."
            )

def find_all_files_under(parent_dir):
    """Recursively finds all files anywhere under the specified directory.

    Returns a list of absolute Path objects. Symlinks are ignored.

    Parameters
    ----------
    parent_dir : str or pathlike object
        The directory under which to recursively find files.

    Raises
    ------
    NotADirectoryError
        Raised if the specified parent directory is not a directory.

    Examples
    --------
    config_files = find_all_files_under("~/.config")

    """

    if "~" in str(parent_dir):
        parent_dir = Path(parent_dir).expanduser()
    parent_dir = Path(parent_dir).resolve()

    if not parent_dir.is_dir():
        raise NotADirectoryError(f"No such directory: '{parent_dir}'.")

    files = []

    for subpath in parent_dir.iterdir():
        if subpath.is_file():
            files.append(subpath.resolve())
        elif not subpath.is_symlink() and subpath.is_dir():
            files += find_all_files_under(subpath)

    return files


def trim_text_file(path_to_input_file, substring):
    """Removes all lines not containing the substring from the input file.

    The input file is overwritten.
    If the substring is the empty string, no action is taken.
    If the substring contains a newline, no action is taken.
    If the substring does not match any line of the file, the resulting file
    will be left empty.

    Parameters
    ----------
    path_to_input_file : str or pathlike object
        The file to trim.
    substring : str
        The string to filter for.
    """

    if not isinstance(substring, str):
        raise TypeError("Expected a string.")
    if "\n" in substring or len(substring) == 0:
        return

    if "~" in str(path_to_input_file):
        path_to_input_file = Path(path_to_input_file).expanduser()
    path_to_input_file = Path(path_to_input_file).resolve()

    if not path_to_input_file.is_file():
        raise FileNotFoundError(f"No such file: '{path_to_input_file}'.")

    # remove unwanted lines from hash file
    input_file = open(path_to_input_file, "r")
    input_file_lines = input_file.readlines()
    input_file_lines_to_keep = []
    for line in input_file_lines:
        if substring in line:
            input_file_lines_to_keep.append(line)
    input_file.close()
    remove(path_to_input_file)
    with open(path_to_input_file, "w") as input_file:
        input_file.writelines(input_file_lines_to_keep)


def file_is_empty(path_to_input_file):
    """Checks whether the input file is empty or not."""

    if "~" in str(path_to_input_file):
        path_to_input_file = Path(path_to_input_file).expanduser()
    path_to_input_file = Path(path_to_input_file).resolve()

    if not path_to_input_file.is_file():
        raise FileNotFoundError(f"No such file: '{path_to_input_file}'.")

    with open(path_to_input_file, 'r') as input_file:
        # try to read a byte
        file_has_content = len(input_file.read(1)) > 0

    return not file_has_content


def download_and_verify_debian_iso(path_to_output_file, printer=None):
    """Downloads the latest Debian ISO as the specified output file.

    The file's integrity is validated using a SHA512 checksum.
    The PGP signature of the SHA512SUMS file is checked using gpg.

    Attributes
    ----------
    path_to_output_file : str or pathlike object
        Path to the file as which the downloaded image will be saved.
    printer : clibella.Printer
        A CLI printer to be used for output.
    """

    if "~" in str(path_to_output_file):
        path_to_output_file = Path(path_to_output_file).expanduser()
    path_to_output_file = Path(path_to_output_file).resolve()

    if path_to_output_file.is_file():
        raise FileExistsError(
            f"Output file '{path_to_output_file}' already exists."
        )
    if not path_to_output_file.parent.is_dir():
        raise NotADirectoryError(
            f"No such directory: '{path_to_output_file.parent}'."
        )

    if printer is None:
        printer = Printer()

    # create a temporary directory
    with TemporaryDirectory() as temp_dir:
        # scrape for URLs and filenames
        files = get_debian_iso_urls()

        # set file paths
        path_to_hash_file = Path(temp_dir)/files["hash_file"]["name"]
        path_to_signature_file = Path(temp_dir)/files["signature_file"]["name"]
        path_to_image_file = Path(temp_dir)/files["image_file"]["name"]

        # download hash file and signature, and verify with gpg
        download_file(
            path_to_hash_file,
            files["hash_file"]["url"],
            show_progress=False,
            printer=printer,
        )
        download_file(
            path_to_signature_file,
            files["signature_file"]["url"],
            show_progress=False,
            printer=printer,
        )

        # verify the hash file using gpg
        printer.info("Verifying hash file using gpg...")
        if not debian_signing_key_is_imported():
            printer.info("Importing Debian public GPG CD signing key...")
            import_debian_signing_key()
        else:
            printer.info("Found Debian public GPG CD signing key.")
        try:
            assert_detached_signature_is_valid(
                path_to_hash_file,
                path_to_signature_file,
            )
        except VerificationFailedError:
            printer.error("PGP signature of the hash file was invalid!")
            exit(1)
        printer.ok("HASH file PGP authenticity check passed.")

        # remove all lines from hash file not containing the image file name
        trim_text_file(path_to_hash_file, files["image_file"]["name"])
        if file_is_empty(path_to_hash_file):
            raise RuntimeError("Failed to locate SHA512 hash sum for image.")

        # download image file
        download_file(
            path_to_image_file,
            files["image_file"]["url"],
            show_progress=True,
            printer=printer,
        )

        # validate SHA512 checksum
        printer.info("Validating ISO file integrity...")
        hash_check_result = run(
            [
                "sha512sum", "--check", path_to_hash_file
            ],
            text=True,
            stdout=PIPE,
            stderr=STDOUT,
            cwd=path_to_image_file.parent,
        )
        if hash_check_result.returncode != 0:
            raise RuntimeError("SHA512 checksum verification of the ISO failed.")
        printer.ok("ISO file integrity check passed.")

        # move downloaded file to specified destination
        rename(path_to_image_file, path_to_output_file)
