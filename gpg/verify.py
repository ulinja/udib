"""Utilities for verifying files using gpg."""

from re import compile
from pathlib import Path
from subprocess import run, PIPE, STDOUT

import gpg.exceptions as ex


def assert_detached_signature_is_valid(
        path_to_input_file,
        path_to_signature_file
):
    """Verifies the input file using the specified detached gpg signature.

    The invoking user's local gpg key store is used for verification, the
    public key used to create the signature must be present in the invoking
    user's local gpg key store.

    Parameters
    ----------
    path_to_input_file : str or pathlike object
        Path to the file which should be verified.
    path_to_signature_file : str or pathlike object
        Path to the file containing a detached gpg signature of the input file.

    Raises
    ------
    FileNotFoundError
        If either of the input files do not exist.
    gpg.exceptions.MissingLocalKeyError
        If a key referenced by the signature file could not be found in the
        invoking user's local key store.
    gpg.exceptions.VerificationFailedError
        If the gpg verification detects a bad signature.
    """

    if '~' in str(path_to_input_file):
        path_to_input_file = Path(path_to_input_file).expanduser()
    path_to_input_file = Path(path_to_input_file).resolve()

    if '~' in str(path_to_signature_file):
        path_to_signature_file = Path(path_to_signature_file).expanduser()
    path_to_signature_file = Path(path_to_signature_file).resolve()

    if not path_to_input_file.is_file():
        raise FileNotFoundError(
            f"No such file: '{path_to_input_file}'."
        )
    if not path_to_signature_file.is_file():
        raise FileNotFoundError(
            f"No such file: '{path_to_signature_file}'."
        )

    # execute a gpg verification as a shell command, redirecting stderr to
    # stdout
    process_result = run(
        [
            "gpg", "--verify", path_to_signature_file, path_to_input_file,
        ],
        stdout=PIPE,
        stderr=STDOUT,
        text=True,
    )
    output_lines = process_result.stdout.split("\n")
    if len(output_lines) < 3:
        raise ex.UnexpectedOutputException(
            f"Unexpected output during gpg verification:\n"
            f"{process_result.stdout}"
        )

    if process_result.returncode == 2:
        # a missing local key causes return code 2
        # and the following output on the third line:
        missing_key_regex = compile(
            r"^gpg: Can't check signature: No public key$"
        )
        # an invalid detached signature file causes return code 2
        # and the following output on the first line:
        invalid_signature_regex = compile(
            r"^gpg: no valid OpenPGP data found.$"
        )

        if missing_key_regex.match(output_lines[2]):
            raise ex.MissingLocalKeyError(
                "Failed to verify gpg signature: no matching local key."
            )
        elif invalid_signature_regex.match(output_lines[0]):
            raise ex.InvalidSignatureError(
                "Invalid signature file."
            )
        else:
            raise ex.UnexpectedOutputException(
                f"Unexpected output during gpg verification:\n"
                f"{process_result.stdout}"
            )
    elif process_result.returncode == 1:
        # failed verification causes return code 1
        # and the following output on line 3:
        verification_failed_regex = compile(
            r"^gpg: BAD signature from .*$"
        )
        if not verification_failed_regex.match(output_lines[2]):
            raise ex.UnexpectedOutputException(
                f"Unexpected output during gpg verification:\n"
                f"{process_result.stdout}"
            )
        else:
            raise ex.VerificationFailedError(
                "gpg signature verification failed: BAD SIGNATURE!"
            )
    elif process_result.returncode == 0:
        # successful verification causes return code 0
        # and the following output on line 3:
        verification_successful_regex = compile(
            r"^gpg: Good signature from .*$"
        )
        if not verification_successful_regex.match(output_lines[2]):
            raise ex.UnexpectedOutputException(
                f"Unexpected output during gpg verification:\n"
                f"{process_result.stdout}"
            )
    else:
        raise ex.UnexpectedOutputException(
            f"Unexpected return code during gpg verification:\n"
            f"{process_result.returncode}"
            f"{process_result.stdout}"
        )
