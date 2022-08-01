"""Utilities for searching and importing GPG keys locally."""

from subprocess import run, STDOUT, PIPE
from re import compile


_DEBIAN_KEY_SERVER_HOSTNAME = "keyring.debian.org"
_DEBIAN_CD_SIGNING_KEY_ID = "DA87E80D6294BE9B"


def import_debian_signing_key():
    """Imports the public debian CD signing key using gpg.

    The key is imported from keyring.debian.org into the invoking user's
    GPG public key store using a shell command.
    """

    # execute a gpg key import as a shell command, redirecting stderr to stdout
    process_result = run(
        [
            "gpg", "--keyserver", _DEBIAN_KEY_SERVER_HOSTNAME,
            "--recv-key", _DEBIAN_CD_SIGNING_KEY_ID
        ],
        stdout=PIPE,
        stderr=STDOUT,
        text=True,
    )

    # check shell return code
    if process_result.returncode != 0:
        if process_result.stdout:
            raise RuntimeError(
                f"Failed to import key using gpg:\n{process_result.stdout}"
            )
        else:
            raise RuntimeError("Failed to import key using gpg.")

    # check shell output:
    # the first line of stdout should look like this
    expected_first_line = str(
        f"gpg: key {_DEBIAN_CD_SIGNING_KEY_ID}: public key "
        f"\"Debian CD signing key <debian-cd@lists.debian.org>\""
        f" imported"
    )

    if not process_result.stdout.split("\n")[0] == expected_first_line:
        raise RuntimeError(
            f"Unexpected output while importing PGP public key:\n"
            f"{process_result.stdout}"
        )


def debian_signing_key_is_imported():
    """Checks whether the debian PGP signing key exists in the local key store.

    The invoking user's GPG key store is checked using a shell command.

    Returns
    -------
    True : bool
        If the public PGP debian cd signing key exists in the invoking user's
        GPG key store.
    False : bool
        If the public PGP debian cd signing key does not exist in the invoking
        user's GPG key store.
    """

    # execute a local gpg key lookup as a shell command, redirecting stderr to
    # stdout
    # NOTE: this command returns 0 even if the key is not present
    process_result = run(
        ["gpg", "--locate-keys", _DEBIAN_CD_SIGNING_KEY_ID],
        stdout=PIPE,
        stderr=STDOUT,
        text=True,
    )

    # check shell return code
    if process_result.returncode != 0:
        raise RuntimeError("Failed to search local keys using gpg.")

    # no shell output means that the key does not exist locally
    if not process_result.stdout:
        return False

    # verify existing key shell output using regex:
    # it should contain six lines in the following format
    expected_output_lines_regexes = [
        compile(r"^pub .*$"),
        compile(r"^ *[0-9A-F]{40}$"),
        compile(r"^uid .*$"),
        compile(r"^sub .*$"),
        compile(r"^$"),
        compile(r"^$"),
    ]

    actual_output_lines = process_result.stdout.split("\n")
    if not len(actual_output_lines) == len(expected_output_lines_regexes):
        raise RuntimeError(
            f"Unexpected line count in shell output while performing local"
            f"GPG key lookup:\n"
            f"{process_result.stdout}"
        )
    for i in range(4):
        if not expected_output_lines_regexes[i].match(actual_output_lines[i]):
            raise RuntimeError(
                f"Unexpected shell output format while performing local"
                f"GPG key lookup:\n"
                f"{process_result.stdout}"
            )

    return True
