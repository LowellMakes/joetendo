This is a work in progress.

- `steam/vent` is the code responsible for launching steam games from
  emulationstation. It also contains an unfinished "first time setup"
  script for adding steam support to an existing emulationstation
  install, but it is not entirely finished and hasn't been tested much
  yet.

- `steam/kiosk` is the code launched at startup, responsible for launching
  steam and emulationstation in a terminal emulator that supports
  background images (xfce4-terminal)

- `steam/menu` are the shell script files that act like "roms" for
  launching steam games from emulationstation. These simple scripts just
  call "vent %appID%". emulationstation learns the name of the game from
  the name of the shell script file.

- `steam/keymaps` are the keymap configuration files for each steam
  game. At the moment, the "common" configuration file is missing and
  will be added to the repository later. They are named after the appID
  for the steam application, which is a little annoying, but very easy
  to code for.

As of time of writing (2025-07-10), these files are manually synced to
the joetendo and there is no "installer" or script to synchronize
them. On the joetendo cabinet, these files are located at:

- `kiosk` is at `/home/nago/bin/kiosk`
- `vent` is at `/home/nago/bin/vent'
- `steam/*` is at `/home/nago/RetroPie/steam`, including the `menu` and
  `keymaps` subdirectories.

As the design of the launcher and accompanying software stabilizes and
solidifies, I hope to automate installation and synchronization so that
new steam games can be added via the git repository, and switch the
"nago" user to the common "maker", and switch the loaded steam account
from my personal account to the LowellMakes community account.

Discussion and planning should occur primarily via the "Arcade and Video
Games" basecamp: https://3.basecamp.com/3376147/projects/1248767