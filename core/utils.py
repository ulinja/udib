"""A collection of general utilities, not specific to any module."""


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
    config_files = _find_all_files_under("~/.config")

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
            files += _find_all_files_under(subpath)

    return files
