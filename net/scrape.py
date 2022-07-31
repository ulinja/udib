"""Methods for scraping the debian website for specific file URLs."""

from re import compile

import requests
from bs4 import BeautifulSoup


def get_debian_preseed_file_urls():
    """Returns a dict containing the URLs for the debian example preseed files.

    The dict has the following structure:
    {
        "basic": {
            "url": "https://...",
            "name": "...",
        },
        "full": {
            "url": "https://...",
            "name": "...",
        },
    }
    where "basic" points to the basic preseed file and its filename, and "full"
    points to the full preseed file and its filename.
    """

    preseed_file_urls = {
        "basic": {
            "url": "https://www.debian.org/releases/stable/example-preseed.txt",
            "name": "example-preseed.txt",
        },
        "full": {
            "url": "https://preseed.debian.net/debian-preseed/bullseye/amd64-main-full.txt",
            "name": "amd64-main-full.txt",
        },
    }

    return preseed_file_urls


def get_debian_iso_urls():
    """Retrieves a dict containing the URLs for a debian installation image.

    The dict has the following structure:
    {
        "image_file": {
            "url": "https://...",
            "name": "debian-xx.x.x-amd64-netinst.iso",
        },
        "hash_file": {
            "url": "https://...",
            "name": "SHA512SUMS",
        },
        "signature_file": {
            "url": "https://...",
            "name": "SHA512SUMS.sign",
        },
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
