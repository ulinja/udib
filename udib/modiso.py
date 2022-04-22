"""Library for modification of disk image files.

Image file modification includes extracting ISO archives, adding files to
initrd-archives contained within the ISO, recalculating md5sum-files
inside the ISO and rebuilding bootable ISOs from directories on the
local filesystem.

"""

from pathlib import Path
import re
import subprocess


def extract_iso(path_to_output_dir, path_to_input_file):
    """Extracts the input ISO-file into the specified directory using 'bsdtar'.

    Source: https://wiki.debian.org/DebianInstaller/Preseed/EditIso#Extracting_the_Initrd_from_an_ISO_Image

    Parameters
    ----------
    path_to_output_dir : str or pathlike object
        Path to the directory into which the contents of the archive will be
        extracted.
    path_to_input_file : str or pathlike object
        Path to the file/archive which should be extracted.

    Raises
    ------
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


def append_file_contents_to_initrd_archive(path_to_initrd_archive,
                                           path_to_input_file):
    """Appends the input file to the specified initrd archive.

    The initrd archive is extracted, the input file is appended, and
    the initrd is repacked again.
    Source: https://wiki.debian.org/DebianInstaller/Preseed/EditIso#Adding_a_Preseed_File_to_the_Initrd

    Parameters
    ----------
    path_to_initrd_archive : str or pathlike object
        Path the the initrd archive to which the input file shall be
        appended. The initrd file must be called 'initrd.gz'.
    path_to_input_file : str or pathlike object
        Path to the input file which shall be added to the initrd
        archive.

    Raises
    ------
    AssertionError
        Thrown if the initrd archive is not named 'initrd.gz'.
    FileNotFoundError
        Thrown if the initrd archive file or input file does not
        exist.

    Examples
    --------
    append_file_contents_to_initrd_archive(
        "/tmp/isofiles/install.386/initrd.gz",
        "/tmp/preseed.cfg")

    """

    path_to_initrd_archive = Path(path_to_initrd_archive)
    path_to_input_file = Path(path_to_input_file)

    # check if initrd file exists and has the correct name
    if not path_to_initrd_archive.is_file():
        raise FileNotFoundError(f"No such file: '{path_to_initrd_archive}'.")
    if not path_to_initrd_archive.name == "initrd.gz":
        raise AssertionError(f"Does not seem to be an initrd.gz archive: "
                             f"'{path_to_initrd_archive.name}'.")

    # check if input file exists
    if not path_to_input_file.is_file():
        raise FileNotFoundError(f"No such file: '{path_to_input_file}'.")

    # temporarily extract initrd archive and append the input file's contents
    try:
        # make archive temporarily writable
        subprocess.run(["chmod", "+w", path_to_initrd_archive],
                       check=True)
        # extract archive in-place
        subprocess.run(["gunzip", path_to_initrd_archive],
                       check=True)
        # append contents of input_file to extracted archive using cpio
        subprocess.run(
            ["echo", path_to_input_file,
             "|", "cpio", "-H", "newc", "-o", "-A",
             "-F", path_to_initrd_archive.with_suffix("")],
            shell=True,
            check=True)
        # repack archive
        subprocess.run(
            ["gzip", path_to_initrd_archive.with_suffix("")],
            check=True)
        # remove write permissions from repacked archive
        subprocess.run(["chmod", "-w", path_to_initrd_archive],
                       check=True)

    except subprocess.CalledProcessError:
        raise RuntimeError(f"Failed while appending contents of "
                           f"'{path_to_input_file}' to "
                           f"'{path_to_initrd_archive}'.")


def regenerate_iso_md5sums_file(path_to_extracted_iso_root):
    """Recalculates and rewrites the md5sum.txt file for the extracted ISO.

    Source: https://wiki.debian.org/DebianInstaller/Preseed/EditIso#Regenerating_md5sum.txt

    Parameters
    ----------
    path_to_extracted_iso_root : str or pathlike object
        Path to the root folder containing an extracted ISO's
        contents.

    Raises
    ------
    RuntimeError
        Raised if the recalculation/rewrite operation fails.
    NotADirectoryError
        Raised if the specified directory is not a directory or does
        not exist.

    Examples
    --------
    regenerate_iso_md5sums_file("/tmp/extracted_iso")

    """

    path_to_extracted_iso_root = Path(path_to_extracted_iso_root)

    # check if input path exists
    if not path_to_extracted_iso_root.is_dir():
        raise NotADirectoryError(f"No such directory: "
                                 f"'{path_to_extracted_iso_root}'.")

    # recalculate and rewrite 'md5sum.txt' in ISO's root
    try:
        # make md5sum.txt temporarily writable
        subprocess.run(
            ["chmod", "+w", path_to_extracted_iso_root/"md5sum.txt"],
            check=True)
        # find all files within ISO's root and regenerate md5sum.txt file
        subprocess.run(
            ["find", path_to_extracted_iso_root,
             "-follow", "-type", "f", "!", "-name", "md5sum.txt", "-print0"
             "|", "xargs", "-0", "md5sum",
             ">", path_to_extracted_iso_root/"md5sum.txt"],
            shell=True,
            check=True)
        # remove write permissions from md5sum.txt
        subprocess.run(
            ["chmod", "-w", path_to_extracted_iso_root/"md5sum.txt"],
            check=True)
    except subprocess.CalledProcessError:
        raise RuntimeError(f"Failed while regenerating "
                           f"'md5sum.txt' within "
                           f"'{path_to_extracted_iso_root}'.")


def extract_mbr_from_iso(path_to_output_file, path_to_source_iso):
    """Extracts the MBR-data from the ISO and writes it into the outputfile.

    The source ISO file must be a BIOS-bootable '.iso'- or
    '.img'-file. You should use a "vanilla" debian installation ISO as
    the source file.

    Source: https://wiki.debian.org/RepackBootableISO#Determine_those_options_which_need_to_be_adapted_on_amd64_or_i386

    Parameters
    ----------
    path_to_output_file : str or pathlike object
        Path to the file which will be created and contain the MBR
        data.
    path_to_source_iso : str or pathlike object
        Path to the source ISO whose MBR data will get extracted.

    Raises
    ------
    RuntimeError
        Raised if the input ISO has the wrong file extension.
    FileNotFoundError
        Raised if the input ISO does not exist or is not a file.
    FileExistsError
        Raised if the output file already exists.

    Examples
    --------
    extract_mbr_from_iso("/tmp/mbr-data.bin", "/tmp/debian-11.0.4-netinst.iso")

    """

    path_to_output_file = Path(path_to_output_file)
    path_to_source_iso = Path(path_to_source_iso)

    # make sure output file does not exist already
    if path_to_output_file.exists():
        raise FileExistsError(
            f"Outputfile exists and would get overwritten: "
            f"'{path_to_output_file}'.")

    # make sure input file exists and has the right extension
    if not path_to_source_iso.is_file():
        raise FileNotFoundError(f"No such file: '{path_to_source_iso}'.")
    if path_to_source_iso.suffix not in [".iso", ".img"]:
        raise RuntimeError(
            f"Input file is not an image file: '{path_to_source_iso}'.")

    # extract the MBR (first 432 Bytes) of the source ISO file
    with open(path_to_source_iso, mode="r+b") as iso_file:
        with open(path_to_output_file, mode="w+b") as mbr_file:
            mbr_file.write(iso_file.read(432))


def repack_iso(path_to_output_iso,
               path_to_mbr_data_file,
               path_to_input_files_root_dir,
               created_iso_filesystem_name):
    """Rebuilds a bootable ISO image using the input files.

    The input files root directory contains the contents of a previously
    extracted ISO file, with its contents possibly modified.
    The MBR data file used should contain MBR data extracted from the
    originially extracted ISO.
    The given filesystem name written into the modified ISO appears when
    the ISO gets mounted. It may only contain alphanumeric characters,
    hyphens, underscores or periods.

    Source: https://wiki.debian.org/RepackBootableISO#Determine_those_options_which_need_to_be_adapted_on_amd64_or_i386

    Parameters
    ----------
    path_to_output_iso : str or pathlike object
        Path to the file as which the created ISO file will be saved.
    path_to_mbr_data_file : str or pathlike object
        Path to an existing file containing MBR data.
    path_to_input_files_root_dir : str or pathlike object
        Path to the root directory of those files which will be repacked into
        the new ISO file.
    created_iso_filesystem_name : str
        Name of the filesystem which the created ISO will have upon
        mounting it.

    Raises
    ------
    RuntimeError
        Raised if the ISO packing process fails.
    NotADirectoryError
        Raised if the specified input files root directory does not
        exist or is not a directory.
    FileNotFoundError
        Raised if the MBR data file does not exist or is not a file.
    FileExistsError
        Raised if the output file already exists.

    Examples
    --------
    repack_iso("/tmp/debian-11.0.4-modified.iso",
        "/tmp/mbr-data.bin",
        "/tmp/extracted-iso",
        "Debian 11.0.4 installation image")

    """

    path_to_output_iso = Path(path_to_output_iso)
    path_to_mbr_data_file = Path(path_to_mbr_data_file)
    path_to_input_files_root_dir = Path(path_to_input_files_root_dir)

    # make sure output file does not exist yet
    if path_to_output_iso.exists():
        raise FileExistsError(f"Existing file would get overwritten: "
                              f"'{path_to_output_iso}'.")

    # make sure input files exist
    if not path_to_mbr_data_file.is_file():
        raise FileNotFoundError(f"No such file: '{path_to_mbr_data_file}'.")
    if not path_to_input_files_root_dir.is_dir():
        raise NotADirectoryError(f"No such directory: "
                                 f"'{path_to_input_files_root_dir}'.")

    # make sure specified filesystem name contains no illegal characters:
    # only alphanumeric, ' ', '.', '_' and '-' are allowed.
    filesystem_name_invalid_char_regex = re.compile(r"[^\w .-]")
    invalid_char_match = filesystem_name_invalid_char_regex.search(
        created_iso_filesystem_name)
    if invalid_char_match is not None:
        raise RuntimeError(f"Invalid character in filesystem name: "
                           f"'{invalid_char_match.group()[0]}'.")

    # repack the ISO using xorriso
    try:
        subprocess.run(
            ["xorriso", "-as", "mkisofs",
             "-r", "-V", created_iso_filesystem_name,
             "-o", path_to_output_iso,
             "-J", "-J", "-joliet-long", "-cache-inodes",
             "-isohybrid-mbr", path_to_mbr_data_file,
             "-b", "isolinux/isolinux.bin",
             "-c", "isolinux/boot.cat",
             "-boot-load-size", "4", "-boot-info-table", "-no-emul-boot",
             "-eltorito-alt-boot",
             "-e", "boot/grub/efi.img", "-no-emul-boot",
             "-isohybrid-gpt-basdat", "-isohybrid-apm-hfsplus",
             path_to_input_files_root_dir],
            check=True)

    except subprocess.CalledProcessError:
        raise RuntimeError(f"Failed while repacking ISO from source files: "
                           f"'{path_to_input_files_root_dir}'.")
