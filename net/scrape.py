"""Methods for scraping the debian website for specific file URLs."""

from re import compile

import requests
from bs4 import BeautifulSoup


def get_debian_iso_urls():
    """Retrieves a dict containing the URLs for a debian installation image.

    The dict has the following structure:
    {
        "image_file":
            "url": "https://...",
            "name": "debian-xx.x.x-amd64-netinst.iso",
        "hash_file":
            "url": "https://...",
            "name": "SHA512SUMS",
        "signature_file":
            "url": "https://...",
            "name": "SHA512SUMS.sign",
    }
    where "image_file" is points to the latest debian stable x86-64bit
    net-installation ISO image, "hash_file" points to a SHA512SUMS file
    containing the SHA512 checksum for the ISO file, and "signature_file"
    points to a file containing a PGP signature for verification of the
    SHA512SUMS file.
    Each top-level dict entry contains a "name" key representing a file name,
    and a "url" key specifying a URL to that file.

    The function scrapes the official debian.org website to retrieve the URLs.
    """

    # request the debian releases page
    releases_url = "https://cdimage.debian.org/debian-cd/current/amd64/iso-cd/"
    releases_page = requests.get(releases_url)
    if not releases_page.status_code == 200:
        raise RuntimeError("Unexpected status code during request.")

    hash_file_name = "SHA512SUMS"
    hash_file_url = releases_url + hash_file_name
    signature_file_name = "SHA512SUMS.sign"
    signature_file_url = releases_url + signature_file_name

    # find the exact URL to the latest stable x64 netinst ISO file
    soup = BeautifulSoup(releases_page.content, "html.parser")
    image_file_links = soup.find_all(
        name="a",
        string=compile(r"debian-[0-9.]*-amd64-netinst.iso")
    )
    if len(image_file_links) != 1:
        raise RuntimeError(
            "Failed to find an exact match while looking for "
            "a link to the latest debian image file."
        )
    image_file_name = image_file_links[0]['href']
    image_file_url = releases_url + image_file_name

    return {
        "image_file": {
            "url": image_file_url,
            "name": image_file_name,
        },
        "hash_file": {
            "url": hash_file_url,
            "name": hash_file_name,
        },
        "signature_file": {
            "url": signature_file_url,
            "name": signature_file_name,
        },
    }


def debian_obtain_image(path_to_output_dir):
    """Downloads the latest debian installation image and its hashes.

    The image file, the SHA512SUMS file it is listed in, as well as the GPG
    signature for the SHA512SUMS file are downloaded from the debian.org HTTPS
    mirrors and written into the specified output directory.
    The obtained image is for the FOSS-only, stable x64 build.

    Once the image file is downloaded, the GPG signature of the hash is
    validated. Then, the hash of the image file is verified. If either check
    fails, an exception is raised.

    If the verification suceeds, the hash file and GPG signature file are
    removed again.

    Parameters
    ----------
    path_to_output_dir : str or pathlike object
        Path to the directory to which all downloaded files will be saved.

    Returns
    -------
    path_to_image_file : str
        Full path to the obtained and validated image file.
    """

    # FIXME download files to a temporary directory
    p.info("Obtaining and verifying the latest Debian stable image...")

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
        raise RuntimeError("Failed to find an exact match while looking for "
                           "a link to the latest debian image file."
                           )
    image_file_name = image_file_links[0]['href']
    image_file_url = releases_url + image_file_name

    # download the SHA512SUMS file
    download_file(path_to_output_dir/hash_file_name, hash_file_url)
    # download the GPG signature file
    download_file(path_to_output_dir/signature_file_name, signature_file_url)

    # verify GPG signature of hash file
    if not gpgverify.gpg_signature_is_valid(
            path_to_output_dir/signature_file_name,
            path_to_output_dir/hash_file_name,
            "keyring.debian.org"
    ):
        raise RuntimeError("GPG signature verification failed!")

    # download the image file
    download_file(path_to_output_dir/image_file_name, image_file_url, True)

    # remove unwanted lines from hash file
    hash_file = open(path_to_output_dir/hash_file_name, "r")
    hash_file_lines = hash_file.readlines()
    hash_file_lines_to_keep = []
    for line in hash_file_lines:
        if image_file_name in line:
            hash_file_lines_to_keep.append(line)
    hash_file.close()
    if len(hash_file_lines_to_keep) != 1:
        raise RuntimeError("Unexpected error while truncating hash file.")
    os.remove(path_to_output_dir/hash_file_name)
    with open(path_to_output_dir/hash_file_name, "w") as hash_file:
        hash_file.writelines(hash_file_lines_to_keep)

    # validate SHA512 checksum
    p.info("Validating file integrity...")
    hash_check_result = subprocess.run(
        ["sha512sum", "--check", path_to_output_dir/hash_file_name],
        capture_output=True,
        cwd=path_to_output_dir
    )

    stdout_lines = hash_check_result.stdout.decode("utf-8").split('\n')
    stderr_lines = hash_check_result.stderr.decode("utf-8").split('\n')

    if len(stdout_lines) > 0:
        for line in stdout_lines:
            if len(line) > 0:
                p.info(f"{line}")

    if hash_check_result.returncode != 0:
        if len(stderr_lines) > 0:
            for line in stderr_lines:
                if len(line) > 0:
                    p.error(f"{line}")
        raise RuntimeError("SHA512 validation failed.")

    p.ok("File integrity checks passed.")

    # clean up obsolete files
    p.info("Cleaning up files...")
    os.remove(path_to_output_dir/hash_file_name)
    os.remove(path_to_output_dir/signature_file_name)

    p.success("Debian image obtained.")

    return path_to_output_dir/image_file_name
