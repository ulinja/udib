# UDIB

UDIB is the Unattended Debian Installation Builder.
It provides a handy commandline utility for injecting files into Debian installation ISOs.
Using UDIB, you can preseed an ISO by injecting a preseed file.
Preseeded ISOs allow fully automated Debian installations on bare metal (or anywhere else).

## Quick Start Guide

This short guide explains how to build a Debian ISO with a customized and automated installation:

1. make sure you have all the [required software](#build-machine) installed
2. clone this repo and `cd` into your local copy
3. (optional) create and activate a virtual environment: `python3 -m venv .venv && . .venv/bin/activate`
4. install the required python packages: `pip install --user -r requirements.txt`
5. download an example preseed file: `./udib.py -o preseed.cfg get preseed-file-basic`
6. customize your installation by editing `preseed.cfg` (the comments are pretty self-explanatory)
7. create a Debian ISO with your preseed file: `./udib.py -o my-image.iso inject preseed.cfg`
8. boot from your newly created ISO `my-image.iso` on your target machine (or in a VM)
9. in the Debian installer menu, navigate to *Advanced options > Automated install*
10. drink some coffee
11. return to your new Debian system

Depending on how many answers you provided in the preseed file, the installation may require some manual interaction.
Preseed files are very powerful, and if you need more customization you can have a deeper look into [how they work](#whats-preseeding).
You can also use UDIB to get the full preseed example file: `./udib.py get preseed-file-full` and use that as a starting point.
Be sure to have a look at the [usage reference](#detailed-usage-guide) for a closer look at UDIB itself.

## What's preseeding?

A preseed file is a text file which provides the Debian installer with previously set (preseeded) answers during the installation process.
Preseeding a Debian ISO allows you to heavily reduce the amount of user interaction required during an installation, or even fully automate it.
The preseed file is written by you and then injected into the installation image.
When you start the installation, any answers you have provided to the debian installer as part of your preseed file are automatically applied during the installation.
If you want to know more, you can have a look at Debian's [official guide](https://www.debian.org/releases/stable/amd64/apb.en.html) or at the Debian wiki's [quick overview](https://wiki.debian.org/DebianInstaller/Preseed), both of which explain preseeding much better than I can.

## How does UDIB work?

UDIB's main purpose is the injection files into existing Debian installation ISOs.
In a nutshell, it does this by extracting the ISO, adding the files to the ISO's initrd, and repacking the ISO again.
You could do all of this manually of course by following the [basic](https://wiki.debian.org/DebianInstaller/Preseed/EditIso#Adding_a_Preseed_File_to_the_Initrd) and [advanced](https://wiki.debian.org/RepackBootableISO) guides for ISO repacking on the Debian wiki, but UDIB does all of this for you.

# Dependencies

Using UDIB to create ISOs requires the following software:

- GNU/Linux
- `python3` *(3.10.4 known to work)*
  - [required python packages](./requirements.txt) can be installed in a virtual environment
- `xorriso` *(1.5.4 known to work)*
  - **Debian (bullseye):** [xorriso](https://packages.debian.org/bullseye/xorriso)
  - **Arch Linux:** [extra/libisoburn](extra/libisoburn)
- GNU `gpg`
  - preinstalled on most distributions
- GNU `cpio`
  - preinstalled on most distributions
- GNU `sha512sum`
  - preinstalled on most distributions

Internet access is (obviously) required if you want to fetch any files using UDIB.

# Detailed usage guide

You can view help at the commandline using `./udib.py --help` for general options and `./udib.py COMMAND --help` for help with a specific subcommand.

The name and destination of files produced by `udib.py` can be specified with the `--output-file` option.
Alternatively, you can use the `--output-dir` option to specify the directory where produced files will be saved, without having to name them explicitly (default names will be used).

## Retrieving example preseed files or vanilla ISOs

As a starting point for creating your own preseeded ISO, you can retrieve one of Debian's example preseed files or an unmodified Debian ISO using UDIB:

```
udib.py [--output-file FILE | --output-dir DIR] get WHAT
```

`WHAT` must be a specific string and can be either one of:

- `preseed-file-basic` to download Debian's basic example preseed file (sufficient in most cases)
- `preseed-file-full` to download Debian's full example preseed file (has a LOT of customization options)
- `iso` to download the latest, unmodified Debian stable x86-64 netinst ISO

## Injecting files into an ISO

To inject existing files into an ISO, you can run the following command:

```
udib.py [--output-file FILE | --output-dir DIR] inject [--image-file IMAGEFILE] FILE [FILE ...]
```

where `FILE` is the path to the file you want to inject.
Injected files are added at the root of the installer's filesystem and can be accessed there during the installation.
**NOTE:** the installer will not recognize a preseed file unless it's filename is `preseed.cfg` exactly.
If you don't specify an `--image-file`, UDIB will download the latest Debian x86-64 netinst ISO and inject your `FILE`s into it.
