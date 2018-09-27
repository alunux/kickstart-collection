%packages

# Exclude unwanted groups that fedora-live-base.ks pulls in
-@dial-up
-@input-methods
-@standard

# Make sure to sync any additions / removals done here with
# workstation-product-environment in comps
@base-x
@core
@fonts
-adobe-source-han-sans-cn-fonts
-adobe-source-han-sans-tw-fonts
-google-noto-sans-*
-lohit-*
-sil-*
-thai-scalable-waree-fonts
@guest-desktop-agents
@hardware-support
@multimedia
@networkmanager-submodules
@printing

# GNOME
NetworkManager-openconnect-gnome
NetworkManager-openvpn-gnome
NetworkManager-ppp
NetworkManager-pptp-gnome
NetworkManager-ssh-gnome
NetworkManager-vpnc-gnome
NetworkManager-wwan
at-spi2-atk
at-spi2-core
dconf
fprintd-pam
gdm
glib-networking
gnome-backgrounds
gnome-bluetooth
gnome-color-manager
gnome-control-center
gnome-disk-utility
gnome-screenshot
gnome-session-wayland-session
gnome-session-xsession
gnome-settings-daemon
gnome-shell
gnome-system-monitor
gnome-terminal
gnome-themes-extra
gnome-user-share
gvfs-afc
gvfs-afp
gvfs-archive
gvfs-fuse
gvfs-goa
gvfs-gphoto2
gvfs-mtp
gvfs-smb
libcanberra-gtk2
libcanberra-gtk3
libproxy-mozjs
librsvg2
libsane-hpaio
mousetweaks
polkit
rygel
sane-backends-drivers-scanners
xdg-desktop-portal
xdg-desktop-portal-gtk
xdg-user-dirs-gtk
yelp
-PackageKit*
# Exclude unwanted packages from @anaconda-tools group
-gfs2-utils
-reiserfs-utils

%end
