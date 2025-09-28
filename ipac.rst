==============================
Current Joetendo IPAC bindings
==============================

The below table maps out the IPac wiring terminals (Port) to the
keypress it is currently configured to send (Keybind). The third
column (Button) lists which physical button on the control deck is
wired to that terminal, if any.

The I-PAC is a discontinued device from Ultimarc, the product
documentation is available through archive.org:
https://web.archive.org/web/20130106004021/https://www.ultimarc.com/ipac1.html

Arcade games (especially through MAME) tend to label their buttons
1-6, while emulated console games tend to label their buttons
ABXYLR. The Joetendo uses emulated console game labeling; so NES, SNES
and GBA games when displaying controller prompts will match the
physical labels. MAME and Steam games may display prompts that don't
correlate physically to the visible labels, there's no real way around
this - you'll just have to try the buttons and see what happens.

Note that these keybinds are merely the "default"; the actual keypress
registered when a button is pushed can in fact be changed by using the
keyd configuration files; this process is documented in the
[adding_games.md](https://github.com/LowellMakes/joetendo/blob/main/adding_games.md)
documentation.


======  ===========  =================================================
Port    Keybind      Button
======  ===========  =================================================
1right  right        Joystick, right
1left   left         Joystick, left
1up     up           Joystick, up
1down   down         Joystick, down
1sw1    leftcontrol  "B" (Bottom row, leftmost)
1sw2    leftalt      "A" (Bottom row, middle)
1sw3    space        "R" (Bottom row, rightmost)
1sw4    leftshift    "Y" (Top row, leftmost)
1sw5    z	     "X" (Top row, middle)
1sw6    x            "L" (Top row, rightmost)
1sw7    c            --
1sw8    v	     --
1strt   1	     "START"
1coin   5	     "SELECT", "COIN"
1a      p	     "EXIT" (Central console, red button)
1b      enter	     --

2right  g            2P joystick, right
2left   d            2P joystick, left
2up     r            2P joystick, up
2down   f            2P joystick, down
2sw1    a            "B" (Bottom row, leftmost)
2sw2    s            "A" (Bottom row, middle)
2sw3    q            "R" (Bottom row, rightmost)
2sw4    w            "Y" (Top row, leftmost)
2sw5    i            "X" (Top row, middle)
2sw6    k            "L" (Top row, rightmost)
2sw7    j            Hidden button inside of control deck
2sw8    l            --
2strt   2            "START"
2coin   6            "SELECT", "COIN"
2a      tab          --
2b      esc          --
======  ===========  =================================================
