# Adding games to Joetendo

Joetendo can be logged into remotely (from within LowellMakes) with
ssh:

```sh
ssh kiosk@joetendo.lowellmakes.lan
```

SFTP is enabled as well, and files can be copied with `scp` or using
e.g. the FileZilla GUI from a Windows computer.

## Adding Emulator games

NES, SNES, GBA, etc games can be added simply by copying the rom file
(It may be compressed, many formats are supported) to the right emulator
subdirectory in `/home/kiosk/RetroPie/roms/`.

For example, you can add "Ninja Gaiden" for the NES by copying "Ninja
Gaiden (USA).zip" to ~/RetroPie/roms/nes/.

Additional detail is available via the [RetroPie
guide](https://retropie.org.uk/docs/Transferring-Roms/), but note that
the SMB/CIFS method is not currently supported by Joetendo, and not all
RetroPie emulators documented may be currently installed or configured.

At the moment, there is no easy way to run the scraper to update the
new game with art and metadata; this presently requires a keyboard
hooked up to Joetendo. The method is to press the "windows key" and
close out of EmulationStation, then open a terminal and type
"emulationstation" with no arguments to re-enable "admin mode" for
EmulationStation, then use the ES menus (press "start") to run the
scraper.

## Adding Steam games

### Get the Steam AppID

To add a Steam game, first you must make sure that the LowellMakes
steam account has access to the game you want to install. From another
LowellMakes computer with Steam installed (Try the computer lab
upstairs!), go to the Steam Library and right-click on the game title
and choose "Properties", then select "Updates" and take note of the
"App ID". For example, Super Hexagon is "221640".

You can also search for the game on steamdb.info; for example Super
Hexagon's page is https://steamdb.info/app/221640/ which prominently
features the appID in the URL and right at the top of the page.

### Run vent-installer

Log in as the kiosk user to Joetendo and run the `vent-installer`
script.

For example, to install Super Hexagon, you would type:

```sh
> vent-installer 221640
```

This will download all of the metadata and game files necessary, and
add the game to the EmulationStation menu.

(Again, this will only work if the LowellMakes steam account has
legitimate access to download and play this game!)

This automatically creates e.g. `/home/kiosk/RetroPie/steam/menu/Super
Hexagon.sh`, adds an entry to
`/home/kiosk/.emulationstation/gamelists/steam/gamelist.xml`, and adds
a template for controller configuration to
`/home/kiosk/RetroPie/steam/keymaps/221640.conf`.

### Configuring controls

The tricky bit is amending the keymap configuration file; here's what
the Super Hexagon configuration file looks like when it is first
generated:

```
# Configuration for Super Hexagon
# Steam appID: 221640

include common

[main]

p1_up = up
p1_down = down
p1_left = left
p1_right = right
p1_1 = leftcontrol
p1_2 = leftalt
p1_3 = space
p1_4 = leftshift
p1_5 = z
p1_6 = x
p1_7 = c
p1_8 = v
p1_a = p
p1_b = enter
p1_coin = 5
p1_start = 1
p2_up = r
p2_down = f
p2_left = d
p2_right = g
p2_1 = a
p2_2 = s
p2_3 = q
p2_4 = w
p2_5 = i
p2_6 = k
p2_7 = j
p2_8 = l
p2_a = tab
p2_b = esc
p2_coin = 6
p2_start = 2
```

This configuration file represents the [default
keybindings](https://github.com/LowellMakes/joetendo/blob/main/ipac.rst)
of Joetendo, and it is highly likely you'll need to adjust them for
the game to actually be playable.

When logged in to Joetendo, you may type `keyd list-keys` to see a
list of recognized key names/spellings accepted by this configuration file.

Here's the actual configuration for Super Hexagon so that the game is
playable:

```
# Configuration for Super Hexagon
# Steam appID: 221640

include common

[main]

p1_up = up
p1_down = down
p1_left = left
p1_right = right

p1_1 = space
p1_2 = space
p1_3 = space
p1_4 = space
p1_5 = space
p1_6 = space

p1_select = esc
p1_start = esc

p2_up = up
p2_down = down
p2_left = left
p2_right = right

p2_1 = space
p2_2 = space
p2_3 = space
p2_4 = space
p2_5 = space
p2_6 = space

p2_select = esc
p2_start = esc
```

Super Hexagon only uses a handful of buttons, so we just map *all* of
the buttons to `space`, and use the start/select buttons as
"esc" to bring up the menu.

If at all possible, it is preferable to write the configuration file
using the *default settings* of the steam game for easy
re-deployment. Some games, like Ikaruga, do not have a default
two-player configuration for a "single keyboard", so sometimes you
*will* have to adjust the game's configuration as well. If you do this,
***please leave a comment in the configuration file explaining what you
had to adjust.***


## Adding arbitrary games

Arbitrary games can be added by adding a launcher script to
`/home/kiosk/RetroPie/steam/menu/`.  It does not matter that it's not
*actually* a steam game.

If your game recognizes the [default Joetendo
keybindings](https://github.com/LowellMakes/joetendo/blob/main/ipac.rst),
this is all you need to do!

If it doesn't, you'll want to create a custom `keyd` configuration file
and manually load and unload it in your custom shell script.

For example, you could create a custom keymap file in
`/home/kiosk/RetroPie/steam/keymaps/MyGame.conf`, using the example
configuration file listed above for Super Hexagon, modifying it to suit
your needs, then your shell script in
`/home/kiosk/RetroPie/steam/menu/MyGame.sh` would need to look like
this:

```sh
#!/usr/bin/env bash

# Load your custom keymap for this game
ln -f -s ~/RetroPie/steam/keymaps/MyGame.conf ~/RetroPie/steam/keymaps/active.conf
keyd reload

# Run your game, however you have to do it. Note that when your game
# exits, control will automatically return to the EmulationStation
# menu.
~/path/to/MyCoolGame.bin

# Load the default keymap back so that when your game exits, the
# EmulationStation menu is navigable:
ln -f -s ~/RetroPie/steam/keymaps/default.conf ~/RetroPie/steam/keymaps/active.conf
keyd reload
```

## What to do when it all goes wrong

If you try to add a game and it doesn't work, please temporarily remove
the game from the EmulationStation menu by renaming the shell script
from ".sh" to ".disabled" so that the menu remains fully functional when
you leave; please don't leave Joetendo in a non-functional state. Reach
out for help on the [Arcade and Video Games
basecamp](https://3.basecamp.com/3376147/projects/1248767)!
