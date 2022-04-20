#!/usr/bin/env python3

""" This module validates GPG signatures for downloaded files. """

from pathlib import Path

import gnupg

import userinput
from printmsg import perror, pfailure, pinfo, pok, psuccess, pwarning

def gpg_signature_is_valid(
        path_to_signature_file,
        path_to_data_file,
        fallback_keyserver_name
):
    """ Validates a PGP signature for a data file. The detached signature is
        provided as plaintext (UTF8) in the specified file.

        If the discovered signing key is unknown to gpg on this system for the
        invoking user, and if 'fallback_keyserver_name' is not None, an attempt
        is made to import the key from the specified keyserver using its ID
        after prompting the user for permission to import the key.

    Parameters
    ----------
    path_to_signature_file : str or pathlike object
        Path to a detached PGP signature stored in a standalone file.
        Example value: "/path/to/SHA256SUMS.sig"
    path_to_data_file : str or pathlike object
        Path to a signed data file, for which the signature is to be verified.
        Example value: "/path/to/SHA256SUMS"
    fallback_keyserver_name : str
        FQDN of a keyserver from which to import unknown public keys.
        Example value: "keyring.debian.org"

    Returns
    -------
    True : bool
        If the signature is valid.
    False : bool
        If the signature is invalid or could not be validated.
    """
    path_to_signature_file = Path(path_to_signature_file)
    path_to_data_file = Path(path_to_data_file)

    gpg = gnupg.GPG()
    gpg.encoding = "utf-8"

    pinfo("Validating signature...")
    with open(path_to_signature_file, "rb") as signature_file:
        verification = gpg.verify_file(
            signature_file,
            path_to_data_file,
            close_file=False
        )

    # check if a key and fingerprint were found in the signature file
    if verification.key_id is None or verification.fingerprint is None:
        raise ValueError(
            f"Not a valid PGP signature file: '{path_to_signature_file}'."
        )
    else:
        pinfo(f"Signature mentions a key with ID "\
              f"{verification.key_id} and fingerprint "\
              f"{verification.fingerprint}."
        )

    if verification.valid:
        pok(f"GPG signature is valid with trustlevel "\
              f"'{verification.trust_level}'."
        )
        return True

    # this case commonly occurrs when the GPG key has not been imported
    if verification.status == "no public key":
        pwarning("Could not find the public GPG key locally!")

        # prompt user until answer is unambiguous
        key_will_be_imported = None
        while key_will_be_imported is None:
            key_will_be_imported = userinput.prompt_yes_or_no(
                f"[PROMPT] Do you want to import the GPG key from "\
                f"'{fallback_keyserver_name}'?"
            )

            if key_will_be_imported is None:
                perror("Unrecognized input. Please try again.")

        if not key_will_be_imported:
            pwarning("Aborting without importing key.")
            return False

        # import missing key
        pinfo("Importing key...")
        import_result = gpg.recv_keys(
            fallback_keyserver_name, verification.key_id
        )

        if import_result.count < 1:
            perror("Failed to import key.")
            return False

        # display some of gpg's output
        gpg_output = import_result.stderr.split('\n')
        for line in gpg_output:
            if line.startswith("gpg: "):
                pinfo(f"{line}")

    # validate signature again
    pinfo("Validating signature...")
    with open(path_to_signature_file, "rb") as signature_file:
        verification = gpg.verify_file(
            signature_file,
            path_to_data_file,
            close_file=False
        )

    if verification.valid:
        pok(f"GPG signature is valid with trustlevel "\
              f"'{verification.trust_level}'."
        )
        return True
    else:
        perror("GPG signature is not valid!!!")
        return False
