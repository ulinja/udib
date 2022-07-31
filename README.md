# UDIB

UDIB is the Unattended Debian Installation Builder.
It provides a handy commandline utility for creating preseeded Debian installation ISOs.
Preseeded ISOs allow partially or fully automated Debian installations on bare metal (or anywhere else).

## What's preseeding?

A preseed file is a text file which provides the Debian installer with previously set (preseeded) answers during the installation process.
Preseeding a Debian ISO allows you to heavily reduce the amount of user interaction required during an installation, or even fully automate it.
The preseed file is written by you and then injected into the installation image.
When you start the installation, any answers you have provided to the debian installer as part of your preseed file are automatically applied during the installation.
If you want to know more, you can have a look at Debian's [official guide](https://www.debian.org/releases/stable/amd64/apb.en.html) or at the Debian wiki's [quick overview](https://wiki.debian.org/DebianInstaller/Preseed), both of which explain preseeding much better than I can.

## How does UDIB work?

UDIB's main purpose is the injection of preseed files into existing Debian installation ISOs.
It does this by extracting the ISO, adding the preseed file to the ISO's initrd, adjusting the ISO's internal file integrity hash list, and finally repacking the ISO and making it bootable.
You could do all of this manually of course by following the [basic](https://wiki.debian.org/DebianInstaller/Preseed/EditIso#Adding_a_Preseed_File_to_the_Initrd) and [advanced](https://wiki.debian.org/RepackBootableISO) guides for ISO repacking on the Debian wiki.
But why would you if I did the work for you, and you can just do it using this simple utility?

# Usage

Besides the injection of preseed files into an ISO, UDIB also allows you to download and verify the latest Debian stable ISO, as well as Debian's example preseed file.

## Retrieving an example preseed file

UDIB ships with a `default-preseedfile.txt` which provides a fully automated Debian installation out of the box.
You can adjust it to your needs in order to customize your installation.
If you don't want to modify UDIB's default preseed file but would rather create your own from scratch, you can retrieve Debian's example preseed file using UDIB:

```bash
udib.py get WHAT [--output-file FILE | --output-dir DIR]
```

`WHAT` can be either one of:

- `preseedfile` to download Debian's example preseed file
- `iso` to download the latest, unmodified Debian stable x86-64 netinst ISO

## Creating a preseeded ISO

To inject an existing preseed file into an ISO, you can run the following command:

```bash
udib.py inject PRESEEDFILE [--image-file IMAGEFILE] [--output-file FILE | --output-dir DIR]
```

where `PRESEEDFILE` is the path to your preseed file.
If you don't specify an `--image-file`, UDIB will download the latest Debian x86-64 netinst ISO and inject your `PRESEEDFILE` into it.
