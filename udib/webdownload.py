#!/usr/bin/env python3

"""This module downloads Debian Linux installation images from the web."""

import os, re, subprocess, zipfile
from pathlib import Path
from datetime import date

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

from printmsg import perror, pfailure, pinfo, pok, psuccess, pwarning
import gpgverify

def download_file(path_to_output_file, url_to_file, show_progress = False):
    """ Downloads the file at the specified URL via HTTP and saves it as the
        specified output file. Optionally, displays a nice status bar.

    Parameters
    ----------
    path_to_output_file : str or pathlike object
        Path to a file as which the downloaded file is saved.
    url_to_file : str
        URL to the file to be downloaded.
    show_progress : bool
        When True, a progress bar is displayed on StdOut indicating the
        progress of the download.
    """

    path_to_output_file = Path(path_to_output_file).resolve()
    if not path_to_output_file.parent.is_dir():
        raise FileNotFoundError(
            f"No such directory: '{path_to_output_file.parent}'."
        )
    if path_to_output_file.exists():
        raise FileExistsError(
            f"File already exists: '{path_to_output_file}'"
        )

    output_file_name = path_to_output_file.name
    with open(path_to_output_file, "wb") as output_file:
        pinfo(f"Downloading '{output_file_name}'...")
        file_response = requests.get(url_to_file, stream=True)
        total_length = file_response.headers.get('content-length')

        if total_length is None: # no content length header
            output_file.write(response.content)
        else:
            if (show_progress):
                total_length = int(total_length)
                progress_bar = tqdm(
                    total=total_length,
                    unit="B",
                    unit_scale=True,
                    unit_divisor=1024
                )

            for data in file_response.iter_content(chunk_size=4096):
                output_file.write(data)
                if (show_progress):
                    progress_bar.update(len(data))

            if (show_progress):
                progress_bar.close()

        pok(f"Received '{output_file_name}'.")

def debian_obtain_image(path_to_output_dir):
    """ Obtains the latest official debian installation image, the SHA512SUMS
        file it is listed in, as well as the GPG signature for the SHA512SUMS
        file.

        File are obtained from the debian.org HTTPS mirrors and stored in the
        specified directory. The obtained image is the FOSS-only, stable x64
        build.

        First, the GPG signature of the hash is validated. Then, the hash of
        the image file is checked. If either check fails, an exception is
        raised.

    Parameters
    ----------
    path_to_output_dir : str or pathlike object
        Path to the directory to which all downloaded files will be saved.

    Returns
    -------
    path_to_image_file : str
        Full path to the obtained and validated image file.
    """

    pinfo("Obtaining and verifying the latest Debian stable image...")

    path_to_output_dir = Path(path_to_output_dir)

    if not path_to_output_dir.is_dir():
        raise ValueError(f"No such directory: '{path_to_output_dir}'")

    releases_url = "https://cdimage.debian.org/debian-cd/current/amd64/iso-cd/"
    releases_page = requests.get(releases_url)
    soup = BeautifulSoup(releases_page.content, "html.parser")

    hash_file_name = "SHA512SUMS"
    hash_file_url = releases_url + hash_file_name
    signature_file_name = "SHA512SUMS.sign"
    signature_file_url = releases_url + signature_file_name

    # find the URL to the latest stable x64 image
    image_file_links = soup.find_all(
        name="a",
        string=re.compile(r"debian-[0-9.]*-amd64-netinst.iso"))
    if len(image_file_links) != 1:
        raise RuntimeError("Failed to find an exact match while looking for "\
            "a link to the latest debian image file.")
    image_file_name = image_file_links[0]['href']
    image_file_url = releases_url + image_file_name

    # download the SHA512SUMS file
    download_file(path_to_output_dir / hash_file_name, hash_file_url)
    # download the GPG signature file
    download_file(path_to_output_dir / signature_file_name, signature_file_url)

    # verify GPG signature of hash file
    if not gpgverify.gpg_signature_is_valid(
            path_to_output_dir / signature_file_name,
            path_to_output_dir / hash_file_name,
            "keyring.debian.org"
    ):
        raise RuntimeError("GPG signature verification failed!")

    # download the image file
    download_file(path_to_output_dir / image_file_name, image_file_url, True)

    # remove unwanted lines from hash file
    hash_file = open(path_to_output_dir / hash_file_name, "r")
    hash_file_lines = hash_file.readlines()
    hash_file_lines_to_keep = []
    for line in hash_file_lines:
        if image_file_name in line:
            hash_file_lines_to_keep.append(line)
    hash_file.close()
    if len(hash_file_lines_to_keep) != 1:
        raise RuntimeError("Unexpected error while truncating hash file.")
    os.remove(path_to_output_dir / hash_file_name)
    with open(path_to_output_dir / hash_file_name, "w") as hash_file:
        hash_file.writelines(hash_file_lines_to_keep)

    # validate SHA512 checksum
    pinfo("Validating file integrity...")
    hash_check_result = subprocess.run(
        ["sha512sum", "--check", path_to_output_dir / hash_file_name],
        capture_output = True,
        cwd = path_to_output_dir
    )

    stdout_lines = hash_check_result.stdout.decode("utf-8").split('\n')
    stderr_lines = hash_check_result.stderr.decode("utf-8").split('\n')

    if len(stdout_lines) > 0:
        for line in stdout_lines:
            if len(line) > 0:
                pinfo(f"{line}")

    if hash_check_result.returncode != 0:
        if len(stderr_lines) > 0:
            for line in stderr_lines:
                if len(line) > 0:
                    perror(f"{line}")
        raise RuntimeError("SHA512 validation failed.")

    pok("File integrity checks passed.")

    # clean up obsolete files
    pinfo("Cleaning up files...")
    os.remove(path_to_output_dir / hash_file_name)
    os.remove(path_to_output_dir / signature_file_name)

    psuccess("Debian image obtained.")

    return str(path_to_output_dir / image_file_name)
