"""Library for downloading files from the web with CLI output."""

from pathlib import Path

import requests
from tqdm import tqdm

from cli.clibella import Printer


def download_file(
        path_to_output_file,
        url_to_file,
        show_progress=False,
        printer=None,
):
    """Downloads the file at the input URL to the specified path.

    The file is downloaded via HTTP/HTTPS and saved to the specified path.
    Optionally, displays a nice status bar.

    Parameters
    ----------
    path_to_output_file : str or pathlike object
        Path to a file as which the downloaded file is saved.
    url_to_file : str
        URL to the file to be downloaded.
    show_progress : bool
        When True, a progress bar is displayed on StdOut indicating the
        progress of the download.
    printer : clibella.Printer
        A clibella.Printer used to print CLI output.
    """

    if '~' in str(path_to_output_file):
        path_to_output_file = Path(path_to_output_file).expanduser()
    path_to_output_file = Path(path_to_output_file).resolve()

    if not path_to_output_file.parent.is_dir():
        raise FileNotFoundError(
            f"No such directory: '{path_to_output_file.parent}'."
        )
    if path_to_output_file.exists():
        raise FileExistsError(
            f"File already exists: '{path_to_output_file}'"
        )

    if printer is None:
        p = Printer()
    else:
        p = printer

    output_file_name = path_to_output_file.name
    with open(path_to_output_file, "wb") as output_file:
        p.info(f"Downloading '{output_file_name}'...")
        file_response = requests.get(url_to_file, stream=True)
        total_length = file_response.headers.get('content-length')

        if total_length is None:  # no content length header
            output_file.write(file_response.content)
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

        p.ok(f"Received '{output_file_name}'.")
