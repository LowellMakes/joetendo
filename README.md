# Joetendo is dead, long live Joetendo

This is a work in progress. License is TBD - currently, "all rights
reserved". Informally, for non-commercial derivatives, please knock
yourself out. For commercial derivatives, please consult
nago@lowellmakes.com.

Joetendo is a community-built custom arcade cabinet in the LowellMakes
makerspace in Lowell, Massachusetts.

Joetendo is currently running Ubuntu 24.04 LTS with RetroPie installed
on an AMD Ryzen NUC-like miniPC. RetroPie uses EmulationStation as its
main launcher interface. The control deck utilizes an iPAC keyboard
device, which is no longer sold. (The
[iPAC2](https://www.ultimarc.com/control-interfaces/i-pacs/i-pac2/) is
the current iteration of the product.)

There have been a number of customizations and addons made to the stock
RetroPie installer. For details, see the
[scripts/deploy.sh](https://github.com/LowellMakes/joetendo/blob/main/scripts/deploy.sh)
script. These customizations include:

  - Using bleeding-edge lr-mame instead of the archaic lr-mame2003, for
    better arcade support
  - Using a [custom fork of EmulationStation](https://github.com/LowellMakes/EmulationStation) that:
    - Disables the main menu when in "kiosk mode"
    - Allows games to be launched with "start" instead of "A"
    - Removes more options from the "select" menu
    - Exports environment variables to launched processes that inform
      them we are in "kiosk mode", so emulators can be configured to
      hide options, too.
  - Disables all GNOME keybinds to prevent conflicts with MAME keybinds
    that might move or resize windows
  - Disables all GNOME notifications and alerts
  - Removes GNOME first-time login screens
  - Removes GNOME power saving and screen timeouts
  - Creates a 'kiosk' user and sets up Ubuntu to automatically log in as
    that account and launch EmulationStation
  - Enables SSH for remote maintenance by the 'maker' user.
  - Sets all RetroPie administration scripts to be "hidden", only when
    in kiosk mode.
  - Modifies the RetroPie run script to disable the emulator
    configuration menus when kiosk mode is enabled, to prevent
    accidentally entering the menu when hitting the A button several
    times during game launch
  - Configures EmulationStation, RetroArch, keyd, and RetroPie input to
    use the ultimarc iPAC controls, based on a single configuration file
    ((steamvent/keycfg.py)[https://github.com/LowellMakes/joetendo/blob/main/steam/steamvent/keycfg.py])
  - Installs and configures Steam support for EmulationStation:
    - Performs initial installation and setup of steamcmd and steam
    - Launches steam invisibly in the background on kiosk launch
    - Adds a new custom "steam" system to `/etc/emulationstation/es_systems.cfg`
    - Installs a custom steam launcher script ("steamvent") responsible
      for launching individual steam games from the ES menu
    - Installs a steam game installer script that fetches art, trailers
      and metadata for a steam game and adds the appropriate keybind
      configuration files and ES menu entries


# Deployment

To deploy this repository and create a new Joetendo:

1. Install Ubuntu 24.04 LTS to a machine. Newer versions might work, but
   haven't been tested. Name the initial admin user something that isn't
   "maker" or "kiosk".

2. Upgrade packages to the latest versions;
   ```sh
   sudo apt-get update && sudo apt-get upgrade -y
   ```

3. Use `wget` and fetch the
   [scripts/deploy.sh](https://github.com/LowellMakes/joetendo/blob/main/scripts/deploy.sh)
   script from this repository:
   ```sh
   wget https://raw.githubusercontent.com/LowellMakes/joetendo/refs/heads/main/scripts/deploy.sh
   ```

4. Mark the script as executable:
   ```sh
   chmod u+x deploy.sh
   ```

5. Run the script with admin privileges:
   ```sh
   sudo ./deploy.sh
   ```

6. Drive 35 minutes away to get your favorite cup of coffee.
   Drive 35 minutes back.

7. If all goes well, you should be greeted with a Steam login prompt
   upon your return. Log in with the LowellMakes credentials. Steam
   *will* ask for 2FA, so you'll need someone who has access to help you
   sign in. After you successfully log in, Steam will exit and the
   deployment script will exit.

8. Reboot! You are now experiencing Super Joetendo.


# Files in this repository

-
  [killswitch/code.py](https://github.com/LowellMakes/joetendo/blob/main/killswitch/code.py)
  is a CircuitPython program written for the Raspberry Pi Pico that
  emulates a keyboard device that when its single button is pressed,
  issues a SysRq "REISUB" request to immediately reboot linux, followed
  by a ctrl+alt+del sequence to reboot the machine if it is in the BIOS
  screen. This powers the "magic reset button" located inside of the
  Joetendo control deck.

-
  [scripts/deploy.sh](https://github.com/LowellMakes/joetendo/blob/main/scripts/deploy.sh)
  is the deployment script that sets everything up. It needs root access
  and expects a pretty much untouched Ubuntu install and an internet
  connection.

-
  [steam/keymaps](https://github.com/LowellMakes/joetendo/tree/main/steam/keymaps)
  houses the keymap configuration files for each steam game. They are
  named after the appID for the steam application, which is a little
  annoying, but very easy to code for. Presently, none of the
  installation or setup scripts copy these configuration files from the
  repo to the `~kiosk/RetroPie/steam/keymaps/` directory, it's a manual
  affair.

  For each game installed using the `vent-installer` script, a default
  keymap file will be generated that can then be edited by hand as
  needed.

-
  [steam/menu](https://github.com/LowellMakes/joetendo/tree/main/steam/menu)
  houses the shell script files that act like "roms" for launching steam
  games from EmulationStation. These simple scripts just call "vent
  %appID%". EmulationStation will use metadata created during steamvent
  install to show art and info about the game. Otherwise, it uses the
  name of the shell script itself.

  Like `steam/keymaps`, these are generated by the steamvent
  installer. At present, none of the installation or setup scripts copy
  the scripts from the repository to `~kiosk/RetroPie/steam/menu/`.

-
  [steam/steamvent/](https://github.com/LowellMakes/joetendo/tree/main/steam/steamvent)
  - This directory houses the steamvent Python package, which provides
  tools for installing and launching Steam games from
  EmulationStation. This package is installed for all users during
  `scripts/deploy.sh`.

-
  [steam/steamvent/setup.py](https://github.com/LowellMakes/joetendo/blob/main/steam/steamvent/setup.py)
  - This script runs during `scripts/deploy.sh` and performs
  Steam-specific initialization of the deployment, including installing
  `steam`, `steamcmd`, and lots of various dependencies.

-
  [steam/steamvent/startup.py](https://github.com/LowellMakes/joetendo/blob/main/steam/steamvent/startup.py)
  - This script provides the `kiosk` and `kiosk-launcher` CLI commands
  that run at startup and are responsible for launching Steam and
  EmulationStation. `kiosk-launcher` effectively just runs `kiosk` in an
  `xfce4-terminal` window to provide support for background images when
  launching steam games. The
  [steam/setup.cfg](https://github.com/LowellMakes/joetendo/blob/main/steam/setup.cfg)
  file names the `kiosk` and `kiosk-launcher` commands and specifies
  which python code each command should run.


# Adding new games to Joetendo

The process of adding new games is documented in detail in the
[adding_games.md](https://github.com/LowellMakes/joetendo/blob/main/adding_games.md)
doc.


# Architecture

A detailed writeup of the architecture and logical flow of the Joetendo
boot process and configuration files is being written and will be added
soon. Please bug nago on basecamp if you have any specific questions in
the meantime!


# Contributing

Discussion and planning should occur primarily via the [Arcade and Video
Games basecamp](https://3.basecamp.com/3376147/projects/1248767).

A new version of the steam launcher script is currently in progress, as
well as additional automation concerning configuring the Steam client.

A major desire is to improve the steam launcher script to track steam
subprocesses better, as certain games (Tetris Effect, in particular) do
not work with the steam launcher as-is and require additional hacks to
work correctly. Some games (Blue Revolver, Tetris Effect) do not respond
particularly well to the Exit button command and do not exit cleanly.

custom artwork and animations are desired for the boot splash logo, the
EmulationStation boot splash screen, the EmulationStation theme itself,
the Joetendo control deck, marquee, and side panels. Get in touch if
you're interested!


# Oh, one more thing

If you're a LowellMakes member and you or a friend have a game you've
made, I'd *love* to put it on the Joetendo. It needs to either run in
Linux or run suitably under wine. For development purposes, if you
target Ubuntu 24.04 LTS, I should be able to get it running on the
cabinet. I'd love to feature your games, no matter how small or silly!

Joetendo controls work by emulating a keyboard; note that the joysticks
are four-switch digital devices and not analog joysticks. If you have
the ability to build your game using the [Joetendo default
keybinds](https://github.com/LowellMakes/joetendo/blob/main/ipac.rst),
you'll have good luck getting it to run suitably on Joetendo.