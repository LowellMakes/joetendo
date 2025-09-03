#!/usr/bin/env bash

set -e

apt install -y git openssh-server figlet make gcc
adduser --comment "kiosk,,," --disabled-password kiosk
adduser --comment "maker,,," --disabled-password maker
echo -e "kiosk:kiosk\nmaker:maker" | chpasswd

mkdir -p src

pushd src
git clone --depth=1 https://github.com/RetroPie/RetroPie-Setup.git
git clone https://github.com/LowellMakes/joetendo.git
git clone https://github.com/jaseg/lolcat.git

pushd lolcat
make
make install
popd

pushd RetroPie-Setup
__user=kiosk ./retropie_packages.sh setup basic_install
popd
popd

# Update the RetroPie menu items to be "hidden", so they do not appear
# in kiosk mode.
xmlstarlet ed -L -s "/gameList/game" -t "elem" -n "hidden" -v "true" \
     /opt/retropie/configs/all/emulationstation/gamelists/retropie/gamelist.xml

# Patch the runcommand script to disable the menu when the ES_KIOSK_MODE
# environment variable is present
patch /opt/retropie/supplementary/runcommand/runcommand.sh <<EOF
--- runcommand.sh	2025-09-03 00:42:58.864857056 -0400
+++ runcommand.sh	2025-09-03 00:51:05.335083012 -0400
@@ -130,6 +130,10 @@
         [[ -z "$LEGACY_JOY2KEY" ]] && LEGACY_JOY2KEY=0
     fi
 
+    if [[ -n "$ES_KIOSK_MODE" ]]; then
+        DISABLE_MENU=1
+    fi
+
     if [[ -n "$DISPLAY" ]] && $XRANDR &>/dev/null; then
         HAS_MODESET="x11"
     # copy kms tool output to global variable to avoid multiple invocations
EOF

# Disable various hotkeys so they don't get accidentally triggered by
# arcade cabinet controls
dconf load '/' <<EOF
[org/gnome/desktop/wm/keybindings]
activate-window-menu=@as []
begin-move=@as []
begin-resize=@as []
close=@as []
cycle-group=@as []
cycle-group-backward=@as []
cycle-panels=@as []
cycle-panels-backward=@as []
cycle-windows=@as []
cycle-windows-backward=@as []
minimize=@as []
move-to-monitor-down=@as []
move-to-monitor-left=@as []
move-to-monitor-right=@as []
move-to-monitor-up=@as []
move-to-workspace-1=@as []
move-to-workspace-last=@as []
move-to-workspace-left=@as []
move-to-workspace-right=@as []
panel-run-dialog=@as []
show-desktop=@as []
switch-applications=@as []
switch-applications-backward=@as []
switch-group=@as []
switch-group-backward=@as []
switch-input-source=@as []
switch-input-source-backward=@as []
switch-panels=@as []
switch-panels-backward=@as []
switch-to-workspace-1=@as []
switch-to-workspace-last=@as []
switch-to-workspace-left=@as []
switch-to-workspace-right=@as []
switch-windows=@as []
switch-windows-backward=@as []
toggle-maximized=@as []

[org/gnome/mutter/keybindings]
toggle-tiled-left=@as []
toggle-tiled-right=@as []

[org/gnome/mutter/wayland/keybindings]
restore-shortcuts=@as []

[org/gnome/settings-daemon/plugins/media-keys]
help=@as []
logout=@as []
magnifier=@as []
magnifier-zoom-in=@as []
magnifier-zoom-out=@as []
screenreader=@as []
screensaver=@as []
terminal=@as []

[org/gnome/shell/keybindings]
focus-active-notification=@as []
screenshot=@as []
screenshot-window=@as []
show-screen-recording-ui=@as []
show-screenshot-ui=@as []
toggle-application-view=@as []
toggle-message-tray=@as []
toggle-quick-settings=@as []

[org/gnome/desktop/notifications]
show-banners=false
show-in-lock-screen=false

[org/gnome/desktop/notifications/application/io-snapcraft-sessionagent]
enable=false
enable-sound-alerts=false

[org/gnome/desktop/notifications/application/nm-applet]
enable=false
enable-sound-alerts=false

[org/gnome/desktop/notifications/application/org-gnome-clocks]
enable=false
enable-sound-alerts=false

[org/gnome/desktop/notifications/application/org-gnome-evolution-alarm-notify]
enable=false
enable-sound-alerts=false

[org/gnome/desktop/notifications/application/org-gnome-nautilus]
enable=false
enable-sound-alerts=false

[org/gnome/desktop/notifications/application/org-gnome-zenity]
enable=false
enable-sound-alerts=false

[org/gnome/desktop/wm/preferences]
num-workspaces=1

[org/gnome/mutter]
dynamic-workspaces=false
edge-tiling=false

[org/gnome/desktop/session]
idle-delay=uint32 0
EOF

# Download and install a figlet font for use with text banners, for funsies
wget http://www.figlet.org/fonts/colossal.flf
install --mode=644 colossal.flf /usr/share/figlet/


#- apply the correct key configurations to emulationstation, retroarch, etc.
# /opt/retropie/configs/all/emulationstation/es_input.cfg
# default es_input.cfg:
# <?xml version="1.0"?>
#<inputList>
#  <inputAction type="onfinish">
#    <command>/opt/retropie/supplementary/emulationstation/scripts/inputconfiguration.sh</command>
#  </inputAction>
#</inputList>

#- change the various settings in emulationstation accordingly
# download the lowellmakes fork of emulationstation and install it
# fix all the various permissions issues here
# run the joetendo steam plugin installer thingie
