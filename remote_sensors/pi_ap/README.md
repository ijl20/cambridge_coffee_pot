# Raspberry Pi with second WiFi interface as an Access Point

This project assumes your Pi has an existing wifi interface (wlan0) but you want to keep
that for the internet connection and install a second (usb) wifi adapter to provide a
'local' SSID. An example use case is for sensors 'downstream' of the Raspberry Pi
to send their data to the Pi.

It is possible to do this using only the inbuilt wifi interface, see https://github.com/peebles/rpi3-wifi-station-ap-stretch
but note this has limitations regarding the wifi channel used.

The example below assumes the following chosen settings, which can be adjusted as required.
```
AP interface: wlan1
AP wifi ssid: CSN-NODE-TEST
AP wifi password: CSN-NODE-TEST
AP wifi channel: 7
AP IP subnet: 192.168.75.0/24
Pi address on AP subnet: 192.168.75.1
```

# USB Wifi Adapter install

The first step is to install the secondary WiFi adapter.

The command `lsusb` should show the device, e.g. as in the top line here:

```
Bus 001 Device 004: ID 2357:0109 TP-Link TL WN823N RTL8192EU
Bus 001 Device 008: ID 413c:2010 Dell Computer Corp. Keyboard
Bus 001 Device 006: ID 413c:1003 Dell Computer Corp. Keyboard Hub
Bus 001 Device 005: ID 046d:c077 Logitech, Inc. M105 Optical Mouse
Bus 001 Device 007: ID 0424:7800 Standard Microsystems Corp. 
Bus 001 Device 003: ID 0424:2514 Standard Microsystems Corp. USB 2.0 Hub
Bus 001 Device 002: ID 0424:2514 Standard Microsystems Corp. USB 2.0 Hub
Bus 001 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub
```

I used a "tp-link 300Mbps Mini Wireless N USB Adapter" TL-WN823N

![tp-link TL-WN823N](tl-wn823n.jpg)

(uses 8192eu driver)

Instructions &  Raspbian drivers at [fars-robotics.net](http://fars-robotics.net) but note
I did **NOT** need to edit my `/etc/interfaces` or `/etc/wpa_supplicant` files.

First step is work out which type of wifi chip is in your USB wifi adapter (by searching
the internet). Eg. in the UK tp-link TL-WN823N it is '8192eu'. Clicking the 
[Directory of available wifi drivers](http://downloads.fars-robotics.net/wifi-drivers/)
gives you a directory-per-driver.

Within the directory (e.g. 
[8192su](http://downloads.fars-robotics.net/wifi-drivers/8192su-drivers/) is the 
long list of available driver versions.

Type `uname -a` to get the version / build number required to select the right file.

Easy install:
```
sudo wget http://fars-robotics.net/install-wifi
sudo chmod +x install-wifi
sudo ./install-wifi
```

At this point you should have a `wlan1` interface.

## dhcpcd.conf

`dhcpcd` is the DHCP *client* for the Raspberry Pi.

```
sudo apt install dhcpcd
```

You need to edit `/etc/dhcpcd.conf` and add an entry for `wlan1` at the end of the file
as below, note that it sets the IP address for the interface as `192.168.75.1`:

```
# A sample configuration for dhcpcd.
# See dhcpcd.conf(5) for details.

# Allow users of this group to interact with dhcpcd via the control socket.
#controlgroup wheel

# Inform the DHCP server of our hostname for DDNS.
hostname

# Use the hardware address of the interface for the Client ID.
clientid
# or
# Use the same DUID + IAID as set in DHCPv6 for DHCPv4 ClientID as per RFC4361.
# Some non-RFC compliant DHCP servers do not reply with this set.
# In this case, comment out duid and enable clientid above.
#duid

# Persist interface configuration when dhcpcd exits.
persistent

# Rapid commit support.
# Safe to enable by default because it requires the equivalent option set
# on the server to actually work.
option rapid_commit

# A list of options to request from the DHCP server.
option domain_name_servers, domain_name, domain_search, host_name
option classless_static_routes
# Most distributions have NTP support.
option ntp_servers
# Respect the network MTU. This is applied to DHCP routes.
option interface_mtu

# A ServerID is required by RFC2131.
require dhcp_server_identifier

# Generate Stable Private IPv6 Addresses instead of hardware based ones
slaac private

# Example static IP configuration:
#interface eth0
#static ip_address=192.168.0.10/24
#static ip6_address=fd51:42f8:caae:d92e::ff/64
#static routers=192.168.0.1
#static domain_name_servers=192.168.0.1 8.8.8.8 fd51:42f8:caae:d92e::1

# It is possible to fall back to a static IP if DHCP fails:
# define static profile
#profile static_eth0
#static ip_address=192.168.1.23/24
#static routers=192.168.1.1
#static domain_name_servers=192.168.1.1

# fallback to static profile on eth0
#interface eth0
#fallback static_eth0

interface wlan0
noipv6 

interface wlan1
static ip_address=192.168.75.1/24
noipv6
nohook wpa_supplicant
```

## hostapd

hostapd is the Linux access point software.

```
sudo apt install hostapd
```

Edit `/etc/hostapd/hostapd.conf` to contain the following, note that is sets ssid and wifi password to CSN-NODE-TEST:

```
# Raspberry Pi wlan1 Access Point
#
interface=wlan1

country_code=GB

driver=nl80211
ssid=CSN-NODE-TEST
hw_mode=g
channel=7
wmm_enabled=0

# Mac-address authentication = accept all (unless deny)
macaddr_acl=0

# Shared key authentication (WEP)
auth_algs=1

# Disable "require stations to know SSID"
ignore_broadcast_ssid=0

wpa=2
wpa_passphrase=CSN-NODE-TEST
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP CCMP
rsn_pairwise=CCMP
logger_syslog=-1
```

## dnsmasq

dnsmasq is the Linux dhcp and dns server. In the example below it is serving the addresses 192.168.75.100 to 200 with
a lease time of 24 hours. Note also it is giving clients the NTP server address of 192.168.75.1 (i.e. the Pi).

`sudo apt install dnsmasq`

Edit `/etc/dnsmasq.conf` to contain:

```
no-resolv

except-interface=wlan0

interface=wlan1
dhcp-range=192.168.75.100,192.168.75.200,255.255.255.0,24h
log-facility=/var/log/dnsmasq.log
log-queries
port=0
dhcp-option=option:ntp-server,192.168.75.1
```

## NTP

NTP is the Linux time server. You can configure this to provide time signals to the subnet served by the Access Point.

Add settings to serve the AP subnet in `/etc/ntp.conf` as the last lines here, so that it serves the time onto only
the subnet (192.168.75.0/24) generated by the Raspberry Pi Access Point.

```
# /etc/ntp.conf, configuration for ntpd; see ntp.conf(5) for help

driftfile /var/lib/ntp/ntp.drift

# Enable this if you want statistics to be logged.
#statsdir /var/log/ntpstats/

statistics loopstats peerstats clockstats
filegen loopstats file loopstats type day enable
filegen peerstats file peerstats type day enable
filegen clockstats file clockstats type day enable


# You do need to talk to an NTP server or two (or three).
#server ntp.your-provider.example

# pool.ntp.org maps to about 1000 low-stratum NTP servers.  Your server will
# pick a different set every time it starts up.  Please consider joining the
# pool: <http://www.pool.ntp.org/join.html>
pool 0.debian.pool.ntp.org iburst
pool 1.debian.pool.ntp.org iburst
pool 2.debian.pool.ntp.org iburst
pool 3.debian.pool.ntp.org iburst


# Access control configuration; see /usr/share/doc/ntp-doc/html/accopt.html for
# details.  The web page <http://support.ntp.org/bin/view/Support/AccessRestrictions>
# might also be helpful.
#
# Note that "restrict" applies to both servers and clients, so a configuration
# that might be intended to block requests from certain clients could also end
# up blocking replies from your own upstream servers.

# By default, exchange time with everybody, but don't allow configuration.
restrict -4 default kod notrap nomodify nopeer noquery limited
restrict -6 default kod notrap nomodify nopeer noquery limited

# Local users may interrogate the ntp server more closely.
restrict 127.0.0.1
restrict ::1

# Needed for adding pool entries
restrict source notrap nomodify noquery

# Clients from this (example!) subnet have unlimited access, but only if
# cryptographically authenticated.
#restrict 192.168.123.0 mask 255.255.255.0 notrust


# If you want to provide time to your local subnet, change the next line.
# (Again, the address is an example only.)
#broadcast 192.168.123.255

# If you want to listen to time broadcasts on your local subnet, de-comment the
# next lines.  Please do this only if you trust everybody on the network!
#disable auth
#broadcastclient

# Added for CSN NODE support
restrict 192.168.75.0 mask 255.255.255.0 nomodify notrap nopeer
broadcast 192.168.75.255
```

# Routing traffic from the AP subnet onwards to the internet.

This is not the subject of this project, but the solution is `iptables` and for clues look here:

https://www.revsys.com/writings/quicktips/nat.html
