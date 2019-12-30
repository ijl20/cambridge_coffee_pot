https://www.raspberrypi.org/documentation/configuration/wireless/access-point.md

<!DOCTYPE html>
<!--[if IE 7]>
<html class="ie ie7" lang="en-GB">
<![endif]-->
<!--[if IE 8]>
<html class="ie ie8" lang="en-GB">
<![endif]-->
<!--[if !(IE 7) | !(IE 8)  ]><!-->
<html lang="en-GB">
<!--<![endif]-->
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, user-scalable=no" />
    <title>Setting up a Raspberry Pi as a Wireless Access Point - Raspberry Pi Documentation</title>
    <meta name="description" content="Documentation in this section includes basic guides to configuring your Raspberry Pi." />
    <link rel="icon" type="image/png" href="/wp-content/themes/mind-control/images/favicon.png" />
    <link rel="publisher" href="https://plus.google.com/+RaspberryPi" />
    <!--[if lt IE 9]>
    <script src="/wp-content/themes/mind-control/js/html5.js"></script>
    <![endif]-->

    <link rel="preconnect stylesheet" href="https://fonts.googleapis.com/css?family=Rubik:300,500,700|Space+Mono|Roboto:300,400,500" media="all" type="text/css">
    <link rel="stylesheet" href="/wp-content/themes/mind-control/css/prism.css" />
    <link rel="stylesheet" href="https://www.raspberrypi.org/app/themes/mind-control/style.min.css?ver=20190621135000" />
    <link rel="stylesheet" href="https://static.raspberrypi.org/styles/hack-font/hack.css">
    <style>
        .entry-content code {
            font-family: Hack, monospace;
        }
    </style>
    <script src="//ajax.googleapis.com/ajax/libs/jquery/1.8.2/jquery.min.js"></script>
    <script src="/wp-content/themes/mind-control/js/jquery.main.js"></script>
    <script src="/wp-content/themes/mind-control/js/prism.js"></script>

    <script type="text/javascript">//<![CDATA[
        var _gaq = _gaq || [];
        _gaq.push(['_setAccount', 'UA-46270871-1']);
        _gaq.push(['_trackPageview']);
        (function () {
            var ga = document.createElement('script');
            ga.type = 'text/javascript';
            ga.async = true;
            ga.src = ('https:' == document.location.protocol ? 'https://ssl' : 'http://www') + '.google-analytics.com/ga.js';

            var s = document.getElementsByTagName('script')[0];
            s.parentNode.insertBefore(ga, s);
        })();
        //]]></script>

    <link rel='canonical' href='https://www.raspberrypi.org/' />
    <link rel='shortlink' href='https://www.raspberrypi.org/' />
</head>

<body class="documentation">
    <header class="o-header">
        <nav class="o-container o-header__container">
            <a class="o-header__home-link" href="/">
                <span class="u-visually-hidden">Home</span>
            </a>

            <div class="o-header__nav">
                <ul class="c-nav">
                                            <li class="c-nav__item">
                            <a
                                class="c-nav__link c-nav__link--products"
                                href="/products/"
                            >
                                Products                            </a>
                        </li>
                                            <li class="c-nav__item">
                            <a
                                class="c-nav__link c-nav__link--blog"
                                href="/blog/"
                            >
                                Blog                            </a>
                        </li>
                                            <li class="c-nav__item">
                            <a
                                class="c-nav__link c-nav__link--downloads"
                                href="/downloads/"
                            >
                                Downloads                            </a>
                        </li>
                                            <li class="c-nav__item">
                            <a
                                class="c-nav__link c-nav__link--community"
                                href="/community/"
                            >
                                Community                            </a>
                        </li>
                                            <li class="c-nav__item">
                            <a
                                class="c-nav__link c-nav__link--help"
                                href="/help/"
                            >
                                Help                            </a>
                        </li>
                                            <li class="c-nav__item">
                            <a
                                class="c-nav__link c-nav__link--forums"
                                href="/forums/"
                            >
                                Forums                            </a>
                        </li>
                                            <li class="c-nav__item">
                            <a
                                class="c-nav__link c-nav__link--education"
                                href="/education/"
                            >
                                Education                            </a>
                        </li>
                                            <li class="c-nav__item">
                            <a
                                class="c-nav__link c-nav__link--projects"
                                href="https://projects.raspberrypi.org/?ref=nav"
                            >
                                Projects                            </a>
                        </li>
                                    </ul>
            </div>

            <div class="o-header__spacer"></div>

            <div class="o-header__search-toggle">
                <span aria-hidden="true" class="c-search-toggle">
                    <span class="u-visually-hidden">Open Search Input</span>
                </span>
            </div>

            <div class="o-header__toggle">
                <span aria-hidden="true" class="c-nav-toggle">
                    <span class="c-nav-toggle__icon">
                        <span class="c-nav-toggle__icon-inner">
                            <span class="u-visually-hidden">Open Navigation</span>
                        </span>
                    </span>
                </span>
            </div>
        </nav>
    </header>

    <div class="o-header__search">
        <form action="/" class="c-search" role="search" method="GET">
            <div class="o-container c-search__container">
                <input type="search" class="c-search__input" placeholder="Search Raspberry Pi" name="s" />
                <button class="c-search__submit">Search</button>
            </div>
        </form>
    </div>

    <script>
        var header = document.querySelector('.o-header')
        var navToggle = document.querySelector('.c-nav-toggle')

        navToggle.addEventListener('click', function (event) {
            event.preventDefault()

            header.classList.toggle('o-header--nav-open')

            document.querySelector('.c-nav-toggle__icon').classList.toggle('c-nav-toggle__icon--open')
            document.querySelector('.c-nav-toggle__icon-inner').classList.toggle('c-nav-toggle__icon-inner--open')
        })

        var searchToggle = document.querySelector('.c-search-toggle')

        searchToggle.addEventListener('click', function (event) {
            event.preventDefault()

            var searchContainer = document.querySelector('.o-header__search')
            var searchInput = document.querySelector('.c-search__input')

            searchInput.blur()
            searchToggle.classList.toggle('c-search-toggle--open')
            searchContainer.classList.toggle('o-header__search--open')

            if (searchContainer.classList.contains('o-header__search--open')) {
                searchInput.focus()
            }
        })
    </script>

    <div class="container">
        <div class="main">

<nav class="breadcrumbs">
    <a href='//www.raspberrypi.org/documentation'>documentation</a> &gt; <a href='//www.raspberrypi.org/documentation/configuration'>configuration</a> &gt; <a href='//www.raspberrypi.org/documentation/configuration/wireless'>wireless</a> &gt; access-point</nav>

<article class="entry-content">
    <h1>Setting up a Raspberry Pi as a Wireless Access Point</h1>
<p>Before proceeding, please ensure your Raspberry Pi is <a href="../../raspbian/updating.md">up to date</a> and rebooted.</p>
<h2>Setting up a Raspberry Pi as an access point in a standalone network (NAT)</h2>
<p>The Raspberry Pi can be used as a wireless access point, running a standalone network. This can be done using the inbuilt wireless features of the Raspberry Pi 3 or Raspberry Pi Zero W, or by using a suitable USB wireless dongle that supports access points.</p>
<p>Note that this documentation was tested on a Raspberry Pi 3, and it is possible that some USB dongles may need slight changes to their settings. If you are having trouble with a USB wireless dongle, please check the forums.</p>
<p>To add a Raspberry Pi-based access point to an existing network, see <a href="#internet-sharing">this section</a>.</p>
<p>In order to work as an access point, the Raspberry Pi will need to have access point software installed, along with DHCP server software to provide connecting devices with a network address.</p>
<p>To create an access point, we'll need DNSMasq and HostAPD. Install all the required software in one go with this command:</p>
<pre><code>sudo apt install dnsmasq hostapd</code></pre>
<p>Since the configuration files are not ready yet, turn the new software off as follows:</p>
<pre><code>sudo systemctl stop dnsmasq
sudo systemctl stop hostapd</code></pre>
<h3>Configuring a static IP</h3>
<p>We are configuring a standalone network to act as a server, so the Raspberry Pi needs to have a static IP address assigned to the wireless port. This documentation assumes that we are using the standard 192.168.x.x IP addresses for our wireless network, so we will assign the server the IP address 192.168.4.1. It is also assumed that the wireless device being used is <code>wlan0</code>.</p>
<p>To configure the static IP address, edit the dhcpcd configuration file with:</p>
<pre><code>sudo nano /etc/dhcpcd.conf</code></pre>
<p>Go to the end of the file and edit it so that it looks like the following:</p>
<pre><code>interface wlan0
    static ip_address=192.168.4.1/24
    nohook wpa_supplicant</code></pre>
<p>Now restart the dhcpcd daemon and set up the new <code>wlan0</code> configuration:</p>
<pre><code>sudo service dhcpcd restart</code></pre>
<h3>Configuring the DHCP server (dnsmasq)</h3>
<p>The DHCP service is provided by dnsmasq. By default, the configuration file contains a lot of information that is not needed, and it is easier to start from scratch. Rename this configuration file, and edit a new one:</p>
<pre><code>sudo mv /etc/dnsmasq.conf /etc/dnsmasq.conf.orig
sudo nano /etc/dnsmasq.conf</code></pre>
<p>Type or copy the following information into the dnsmasq configuration file and save it:</p>
<pre><code>interface=wlan0      # Use the require wireless interface - usually wlan0
dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h</code></pre>
<p>So for <code>wlan0</code>, we are going to provide IP addresses between 192.168.4.2 and 192.168.4.20, with a lease time of 24 hours. If you are providing DHCP services for other network devices (e.g. eth0), you could add more sections with the appropriate interface header, with the range of addresses you intend to provide to that interface.</p>
<p>There are many more options for dnsmasq; see the <a href="http://www.thekelleys.org.uk/dnsmasq/doc.html">dnsmasq documentation</a> for more details.</p>
<p>Reload <code>dnsmasq</code> to use the updated configuration:</p>
<pre><code>sudo systemctl reload dnsmasq</code></pre>
<p><a name="hostapd-config"></a></p>
<h3>Configuring the access point host software (hostapd)</h3>
<p>You need to edit the hostapd configuration file, located at /etc/hostapd/hostapd.conf, to add the various parameters for your wireless network. After initial install, this will be a new/empty file.</p>
<pre><code>sudo nano /etc/hostapd/hostapd.conf</code></pre>
<p>Add the information below to the configuration file. This configuration assumes we are using channel 7, with a network name of NameOfNetwork, and a password AardvarkBadgerHedgehog. Note that the name and password should <strong>not</strong> have quotes around them. The passphrase should be between 8 and 64 characters in length.</p>
<p>To use the 5 GHz band, you can change the operations mode from hw_mode=g to hw_mode=a. Possible values for hw_mode are:</p>
<ul>
<li>a = IEEE 802.11a (5 GHz)</li>
<li>b = IEEE 802.11b (2.4 GHz)</li>
<li>g = IEEE 802.11g (2.4 GHz)</li>
<li>ad = IEEE 802.11ad (60 GHz) (Not available on the Raspberry Pi)</li>
</ul>
<pre><code>interface=wlan0
driver=nl80211
ssid=NameOfNetwork
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=AardvarkBadgerHedgehog
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP</code></pre>
<p>We now need to tell the system where to find this configuration file.</p>
<pre><code>sudo nano /etc/default/hostapd</code></pre>
<p>Find the line with #DAEMON_CONF, and replace it with this:</p>
<pre><code>DAEMON_CONF="/etc/hostapd/hostapd.conf"</code></pre>
<h3>Start it up</h3>
<p>Now enable and start <code>hostapd</code>:</p>
<pre><code>sudo systemctl unmask hostapd
sudo systemctl enable hostapd
sudo systemctl start hostapd</code></pre>
<p>Do a quick check of their status to ensure they are active and running:</p>
<pre><code>sudo systemctl status hostapd
sudo systemctl status dnsmasq</code></pre>
<h3>Add routing and masquerade</h3>
<p>Edit /etc/sysctl.conf and uncomment this line:</p>
<pre><code>net.ipv4.ip_forward=1</code></pre>
<p>Add a masquerade for outbound traffic on eth0:</p>
<pre><code>sudo iptables -t nat -A  POSTROUTING -o eth0 -j MASQUERADE</code></pre>
<p>Save the iptables rule.</p>
<pre><code>sudo sh -c "iptables-save &gt; /etc/iptables.ipv4.nat"</code></pre>
<p>Edit /etc/rc.local and add this just above "exit 0" to install these rules on boot.</p>
<pre><code>iptables-restore &lt; /etc/iptables.ipv4.nat</code></pre>
<p>Reboot and ensure it still functions.</p>
<p>Using a wireless device, search for networks. The network SSID you specified in the hostapd configuration should now be present, and it should be accessible with the specified password.</p>
<p>If SSH is enabled on the Raspberry Pi access point, it should be possible to connect to it from another Linux box (or a system with SSH connectivity present) as follows, assuming the <code>pi</code> account is present:</p>
<pre><code>ssh <a href="/cdn-cgi/l/email-protection" class="__cf_email__" data-cfemail="73031a33424a415d42454b5d475d42">[email&#160;protected]</a></code></pre>
<p>By this point, the Raspberry Pi is acting as an access point, and other devices can associate with it. Associated devices can access the Raspberry Pi access point via its IP address for operations such as <code>rsync</code>, <code>scp</code>, or <code>ssh</code>.</p>
<p><a name="internet-sharing"></a></p>
<h2>Using the Raspberry Pi as an access point to share an internet connection (bridge)</h2>
<p>One common use of the Raspberry Pi as an access point is to provide wireless connections to a wired Ethernet connection, so that anyone logged into the access point can access the internet, providing of course that the wired Ethernet on the Pi can connect to the internet via some sort of router.</p>
<p>To do this, a 'bridge' needs to put in place between the wireless device and the Ethernet device on the access point Raspberry Pi. This bridge will pass all traffic between the two interfaces. Install the following packages to enable the access point setup and bridging.</p>
<pre><code>sudo apt install hostapd bridge-utils</code></pre>
<p>Since the configuration files are not ready yet, turn the new software off as follows:</p>
<pre><code>sudo systemctl stop hostapd</code></pre>
<p>Bridging creates a higher-level construct over the two ports being bridged. It is the bridge that is the network device, so we need to stop the <code>eth0</code> and <code>wlan0</code> ports being allocated IP addresses by the DHCP client on the Raspberry Pi.</p>
<pre><code>sudo nano /etc/dhcpcd.conf</code></pre>
<p>Add <code>denyinterfaces wlan0</code> and <code>denyinterfaces eth0</code> to the end of the file (but above any other added <code>interface</code> lines) and save the file.</p>
<p>Add a new bridge, which in this case is called <code>br0</code>.</p>
<pre><code>sudo brctl addbr br0</code></pre>
<p>Connect the network ports. In this case, connect <code>eth0</code> to the bridge <code>br0</code>.</p>
<pre><code>sudo brctl addif br0 eth0</code></pre>
<p>Now the interfaces file needs to be edited to adjust the various devices to work with bridging. To make this work with the newer systemd configuration options, you'll need to create a set of network configuration files.</p>
<p>If you want to create a Linux bridge (br0) and add a physical interface (eth0) to the bridge, create the following configuration.</p>
<pre><code>sudo nano /etc/systemd/network/bridge-br0.netdev

[NetDev]
Name=br0
Kind=bridge</code></pre>
<p>Then configure the bridge interface br0 and the slave interface eth0 using .network files as follows:</p>
<pre><code>sudo nano /etc/systemd/network/bridge-br0-slave.network

[Match]
Name=eth0

[Network]
Bridge=br0</code></pre>
<pre><code>sudo nano /etc/systemd/network/bridge-br0.network

[Match]
Name=br0

[Network]
Address=192.168.10.100/24
Gateway=192.168.10.1
DNS=8.8.8.8</code></pre>
<p>Finally, restart systemd-networkd:</p>
<pre><code>sudo systemctl restart systemd-networkd</code></pre>
<p>You can also use the brctl tool to verify that a bridge br0 has been created.</p>
<p>The access point setup is almost the same as that shown in the previous section. Follow the instructions above to set up the <code>hostapd.conf</code> file, but add <code>bridge=br0</code> below the <code>interface=wlan0</code> line, and remove or comment out the driver line. The passphrase must be between 8 and 64 characters long.</p>
<p>To use the 5 GHz band, you can change the operations mode from 'hw_mode=g' to 'hw_mode=a'. The possible values for hw_mode are:</p>
<ul>
<li>a = IEEE 802.11a (5 GHz)</li>
<li>b = IEEE 802.11b (2.4 GHz)</li>
<li>g = IEEE 802.11g (2.4 GHz)</li>
<li>ad = IEEE 802.11ad (60 GHz) (Not available on the Raspberry Pi)</li>
</ul>
<pre><code>interface=wlan0
bridge=br0
#driver=nl80211
ssid=NameOfNetwork
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=AardvarkBadgerHedgehog
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP</code></pre>
<p>Now reboot the Raspberry Pi.</p>
<pre><code>sudo systemctl unmask hostapd
sudo systemctl enable hostapd
sudo systemctl start hostapd</code></pre>
<p>There should now be a functioning bridge between the wireless LAN and the Ethernet connection on the Raspberry Pi, and any device associated with the Raspberry Pi access point will act as if it is connected to the access point's wired Ethernet.</p>
<p>The bridge will have been allocated an IP address via the wired Ethernet's DHCP server. Do a quick check of the network interfaces configuration via:</p>
<pre><code>ip addr</code></pre>
<p>The <code>wlan0</code> and <code>eth0</code> no longer have IP addresses, as they are now controlled by the bridge. It is possible to use a static IP address for the bridge if required, but generally, if the Raspberry Pi access point is connected to an ADSL router, the DHCP address will be fine.</p></article>

                <footer class="licence">
                    <aside class="octocat">
                        <a href="https://github.com/raspberrypi/documentation/blob/master/configuration/wireless/access-point.md"><img src="/wp-content/themes/mind-control/images/octocat.jpg" /></a>
                    </aside>
                    <aside class="links">
                        <a href="https://github.com/raspberrypi/documentation/blob/master/configuration/wireless/access-point.md" class="github">View/Edit this page on GitHub</a><br />
                        <a href="/creative-commons/">Read our usage and contributions policy</a><br />
                        <a href="/creative-commons/" class="cc"><img src="//i.creativecommons.org/l/by-sa/4.0/88x31.png" alt="Creative Commons Licence"></a>
                    </aside>
                </footer>

                <div style="clear: both;"></div>

            </div>

        <div style="clear: both;"></div>
    </div>

    <footer class="o-footer">
        <div class="o-footer__slice">
            <div class="o-footer__container">
                <div class="o-footer__nav">
                    <div class="c-footer-nav">
                        <span class="c-footer-nav__title">About Us</span>

                        <ul class="c-footer-nav__list">
                            <li class="c-footer-nav__item">
                                <a class="c-footer-nav__link" href="/about">About us</a>
                            </li>
                            <li class="c-footer-nav__item">
                                <a class="c-footer-nav__link" href="/about/meet-the-team">Our team</a>
                            </li>
                            <li class="c-footer-nav__item">
                                <a class="c-footer-nav__link" href="/about/governance">Governance</a>
                            </li>
                            <li class="c-footer-nav__item">
                                <a class="c-footer-nav__link" href="/safeguarding">Safeguarding</a>
                            </li>
                            <li class="c-footer-nav__item">
                                <a class="c-footer-nav__link" href="/about/supporters">Our supporters</a>
                            </li>
                            <li class="c-footer-nav__item">
                                <a class="c-footer-nav__link" href="https://raspberrypi.workable.com/">Jobs</a>
                            </li>
                            <li class="c-footer-nav__item">
                                <a class="c-footer-nav__link" href="/contact">Contact us</a>
                            </li>
                        </ul>
                    </div>
                </div>

                <div class="o-footer__nav">
                    <div class="c-footer-nav">
                        <span class="c-footer-nav__title">Support</span>

                        <ul class="c-footer-nav__list">
                            <li class="c-footer-nav__item">
                                <a class="c-footer-nav__link" href="/help">Help</a>
                            </li>
                            <li class="c-footer-nav__item">
                                <a class="c-footer-nav__link" href="/documentation">Documentation</a>
                            </li>
                            <li class="c-footer-nav__item">
                                <a class="c-footer-nav__link" href="https://projects.raspberrypi.org/">Projects</a>
                            </li>
                            <li class="c-footer-nav__item">
                                <a class="c-footer-nav__link" href="/training">Training</a>
                            </li>
                            <li class="c-footer-nav__item">
                                <a class="c-footer-nav__link" href="/downloads">Downloads</a>
                            </li>
                            <li class="c-footer-nav__item">
                                <a class="c-footer-nav__link" href="/research-and-insights">Research</a>
                            </li>
                            <li class="c-footer-nav__item">
                                <a class="c-footer-nav__link" href="/help/faqs">FAQ</a>
                            </li>
                        </ul>
                    </div>
                </div>

                <div class="o-footer__newsletter">
                    <form
                        action="https://raspberrypi.hosted.phplist.com/lists/?p=subscribe&amp;id=1"
                        class="c-footer-newsletter"
                        method="POST"
                    >
                        <span class="c-footer-newsletter__legend">
                            Sign up to our newsletter
                        </span>
                        <input
                            class="c-footer-newsletter__input"
                            name="email"
                            placeholder="Your email here"
                            required
                            type="email"
                        />
                        <input type="hidden" name="htmlemail" value="1" />
                        <input type="hidden" name="list[3]" value="signup" />
                        <input type="hidden" name="listname[3]" value="Raspberry Pi Weekly" />
                        <input
                            class="c-footer-newsletter__input--verification-code"
                            type="text"
                            name="VerificationCodeX"
                            value=""
                            size="20"
                        />
                        <button class="c-footer-newsletter__button" name="subscribe">
                            Subscribe
                        </button>
                    </form>
                </div>

                <div class="o-footer__info">
                    <ul class="c-footer-social">
                        <li class="c-footer-social__item">
                            <a class="c-footer-social__link c-footer-social__link--facebook" href="https://www.facebook.com/raspberrypi">
                                <span class="u-visually-hidden">Like Raspberry Pi on Facebook</span>
                            </a>
                        </li>
                        <li class="c-footer-social__item">
                            <a class="c-footer-social__link c-footer-social__link--twitter" href="https://twitter.com/Raspberry_Pi">
                                <span class="u-visually-hidden">Follow Raspberry Pi on Twitter</span>
                            </a>
                        </li>
                        <li class="c-footer-social__item">
                            <a class="c-footer-social__link c-footer-social__link--instagram" href="https://www.instagram.com/raspberrypifoundation/">
                                <span class="u-visually-hidden">Check out what we’re having for lunch on Instagram</span>
                            </a>
                        </li>
                        <li class="c-footer-social__item">
                            <a class="c-footer-social__link c-footer-social__link--youtube" href="https://youtube.com/raspberrypi">
                                <span class="u-visually-hidden">Subscribe to the Raspberry Pi YouTube channel</span>
                            </a>
                        </li>
                    </ul>

                    <p class="c-footer-charity">
                        Raspberry Pi Foundation<br>
                        UK Registered Charity 1129409
                    </p>

                    <p class="c-footer-additional">
                        <a class="c-footer-additional__link" href="/privacy">Privacy</a>
                        <a class="c-footer-additional__link" href="/cookies">Cookies</a>
                        <a class="c-footer-additional__link" href="/trademark-rules">Trademark rules and brand guidelines</a>
                    </p>
                </div>
            </div>
        </div>
    </footer>
<script data-cfasync="false" src="/cdn-cgi/scripts/5c5dd728/cloudflare-static/email-decode.min.js"></script></body>
</html>
