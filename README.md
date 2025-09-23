# Joetendo is dead, long live Joetendo

This is a work in progress. License is TBD - currently, "all rights
reserved". Informally, for non-commercial derivatives, please knock
yourself out. For commercial derivatives, please consult
nago@lowellmakes.com.

Joetendo is currently running Ubuntu 24.04 LTS with RetroPie installed
on an AMD Ryzen NUC-like miniPC. RetroPie uses EmulationStation as its
main launcher interface. The control deck utilizes an iPAC keyboard
device, which is no longer sold. (The
[iPAC2](https://www.ultimarc.com/control-interfaces/i-pacs/i-pac2/) is
the current iteration of the product.)

There have been a number of customizations and addons made to the stock
RetroPie installer. For details, see the `scripts/deploy.sh`
script. These customizations include:

  - Using bleeding-edge lr-mame instead of the archaic lr-mame2003, for
    better arcade support
  - Using a custom fork of EmulationStation that:
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
    use the ultimarc iPAC controls, based on a single configuration
    file (`steamvent/keycfg.py`)
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
   sudo apt-get update && sudo apt-get upgrade -y

3. Use wget and fetch the scripts/deploy.sh script from this repository:
   wget https://raw.githubusercontent.com/LowellMakes/joetendo/refs/heads/main/scripts/deploy.sh

4. Set the script executable
   chmod u+x deploy.sh

5. Run the script with admin privileges
   sudo ./deploy.sh

6. Drive 35 minutes away to get your favorite cup of coffee.
   Drive 35 minutes back.

7. If all goes well, you should be greeted with a Steam login prompt
   upon your return. Log in with the LowellMakes credentials. Steam
   *will* ask for 2FA, you'll need someone who has access to help you
   sign in. After you successfully log in, Steam will exit and the
   deployment script will exit.

8. Reboot! You are now experiencing Super Joetendo.


# Files in this repository

- `killswitch/code.py` is a CircuitPython program written for the
  Raspberry Pi Pico that emulates a keyboard device that when its single
  button is pressed, issues a SysRq "REISUB" request to immediately
  reboot linux, followed by a ctrl+alt+del sequence to reboot the
  machine if it is in the BIOS screen. This powers the "magic reset
  button" located inside of the Joetendo control deck.

- `scripts/deploy.sh` is the deployment script that sets everything
  up. It needs root access and expects a pretty much untouched Ubuntu
  install and an internet connection.

- `steam/keymaps` are the keymap configuration files for each steam
  game. They are named after the appID for the steam application, which
  is a little annoying, but very easy to code for. Presently, none of
  the installation or setup scripts copy these configuration files from
  the repo to the `~kiosk/RetroPie/steam/keymaps/` directory, it's a
  manual affair.

  For each game installed using the steamvent installer script, a
  default keymap file will be generated that can then be edited by hand
  as needed.

- `steam/menu` houses the shell script files that act like "roms" for
  launching steam games from EmulationStation. These simple scripts just
  call "vent %appID%". EmulationStation will use metadata created during
  steamvent install to show art and info about the game. Otherwise, it
  uses the name of the shell script itself.

  Like `steam/keymaps`, these are generated by the steamvent
  installer. At present, none of the installation or setup scripts copy
  the scripts from the repository to `~kiosk/RetroPie/steam/menu/`.

- `steam/steamvent/` - This directory houses the steamvent Python
  package, which provides tools for installing and launching Steam games
  from EmulationStation. This package is installed during
  `scripts/deploy.sh`.

- `steam/steamvent/setup.py` - This script runs during
  `scripts/deploy.sh` and performs Steam-specific initialization of the
  deployment.

- `steam/steamvent/startup.py` - This script provides the `kiosk` and
  `kiosk-launcher` command line scripts that run at startup and are
  responsible for launching Steam and EmulationStation. kiosk-launcher
  effectively just runs `kiosk` in an `xfce4-terminal` window to provide
  support for background images when launching steam games. The
  `steam/steamvent/setup.cfg` file names the `kiosk` and
  `kiosk-launcher` commands and specifies which python code each command
  should run.


# Configuration

At the heart of it, this is EmulationStation + RetroPie plus a few new
bells and whistles. Most configuration can be found at
`/opt/retropie/configs`, but keep in mind that this directory is
effectively owned by the kiosk user and should not be considered global
configuration.

EmulationStation system configuration can be found at
`/etc/emulationstation/es_systems.cfg`. This file is where Steam support
has been added, with an XML entry like the following:

```
    <system>
      <name>steam</name>
      <fullname>Steam</fullname>
      <path>/home/kiosk/RetroPie/steam/menu</path>
      <extension>.sh</extension>
      <command>%ROM%</command>
      <platform>steam</platform>
      <theme>steam</theme>
    </system>
```

We configure EmulationStation to believe the ".sh" files in the
steam/menu directory are "roms", and we launch them just by running the
"rom" as an executable command (`%ROM%`). These shell script "roms"
simply call out to the "vent" executable, which is the actual steam game
launcher that makes the magic happen.

Additional games can be added to the `~kiosk/RetroPie/steam/menu`
directory as shell scripts.


# Future

I have plans to add a new version of the steam launcher and the
steamvent installer script, alongside documentation for the
game-addition process. Sit tight until then, please!

Discussion and planning should occur primarily via the "Arcade and Video
Games" basecamp: https://3.basecamp.com/3376147/projects/1248767


# Oh, one more thing

If you're a LowellMakes member and you or a friend have a game you've
made, I'd *love* to put it on the Joetendo. It needs to either run in
Linux or run suitably under wine. For development purposes, if you
target Ubuntu 24.04 LTS, I should be able to get it running on the
cabinet. I'd love to feature your games, no matter how small or silly!
