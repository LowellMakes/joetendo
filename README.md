# Joetendo is dead, long live Joetendo

This is a work in progress. License is TBD - currently, "all rights
reserved". Informally, for non-commercial derivatives, please knock
yourself out. For commercial derivatives, please consult
nago@lowellmakes.com.

Joetendo is currently running Ubuntu 24.04 LTS with RetroPie installed
on an Intel NUC-like PC. RetroPie uses EmulationStation as its main
launcher interface. The control deck utilizes an iPAC keyboard device,
which is no longer sold. The iPAC2 is the current iteration of the
product: https://www.ultimarc.com/control-interfaces/i-pacs/i-pac2/

The majority of bespoke customizations made to RetroPie/EmulationStation
on the Joetendo are in the form of the "vent" steam launcher script.
Other notable tweaks from the "default" are:

  - GNOME hotkeys have been disabled to prevent arcade controls from
    accidentally triggering window movement hotkeys.

  - The bootup script for RetroPie (accessible via GNOME settings menu)
    has been changed to the `~/bin/kiosk` auto-launcher script which
    facilitates launching steam in conjunction with EmulationStation, as
    well as forcing EmulationStation into "kiosk" mode, which removes
    the majority of administration and configuration menus to prevent
    users from accidentally changing the known good settings.

  - The RetroPie maintenance menu which is normally visible as a
    "system" in the EmulationStation launcher has been removed from
    `/etc/emulationstation/es_systems.cfg`, again to prevent accidental
    misconfiguration by end users.

  - The default MAME emulator packaged as part of RetroPie is forked
    from the 2003 version. We have compiled and enabled the "bleeding
    edge" MAME emulator instead for increased support and better
    emulation on a number of arcade titles.

Currently, Joetendo runs as the "nago" user. For SSH access, please ping
nago on basecamp and give them your public SSH key for access.


# Files in this repository

- `steam/vent` is the code responsible for launching steam games from
  emulationstation. It also contains an unfinished "first time setup"
  script for adding steam support to an existing emulationstation
  install, but it is not entirely finished and hasn't been tested much
  yet.

- `steam/kiosk` is the code launched at startup, responsible for launching
  steam and emulationstation in a terminal emulator that supports
  background images (xfce4-terminal)

- `steam/menu` houses the shell script files that act like "roms" for
  launching steam games from emulationstation. These simple scripts just
  call "vent %appID%". emulationstation learns the name of the game from
  the name of the shell script file.

- `steam/keymaps` are the keymap configuration files for each steam
  game. At the moment, the "common" configuration file is missing and
  will be added to the repository later. They are named after the appID
  for the steam application, which is a little annoying, but very easy
  to code for.


# Deployment

As of time of writing (2025-07-10), these files are manually synced to
the joetendo and there is no "installer" or script to synchronize
them. On the joetendo cabinet, these files are located at:

- `kiosk` is at `/home/nago/bin/kiosk`
- `vent` is at `/home/nago/bin/vent'
- `steam/*` is at `/home/nago/RetroPie/steam`, including the `menu` and
  `keymaps` subdirectories.

EmulationStation configuration is in
`/etc/emulationstation/es_systems.cfg`, to which we have added a custom
"steam" system:

```
    <system>
      <name>steam</name>
      <fullname>Steam</fullname>
      <path>/home/nago/RetroPie/steam/menu</path>
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

# Future

As the design of the launcher and accompanying software stabilizes and
solidifies, I hope to automate installation and synchronization so that
new steam games can be added via the git repository, and switch the
"nago" user to two separate accounts, "maker" for administration tasks
and "kiosk" as the unprivileged runtime account that powers the cabinet.

I also intend to switch the loaded steam account from my *personal*
account to the LowellMakes community account, allowing for
community-driven maintenance and game curation for the joetendo cabinet.

Discussion and planning should occur primarily via the "Arcade and Video
Games" basecamp: https://3.basecamp.com/3376147/projects/1248767

# Oh, one more thing

If you're a LowellMakes member and you or a friend have a game you've
made, I'd *love* to put it on the Joetendo. It needs to either run in
Linux or run suitably under wine. For development purposes, if you
target Ubuntu 24.04 LTS, I should be able to get it running on the
cabinet. I'd love to feature your games, no matter how small or silly!
