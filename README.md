Status
------

This project is under development.

This documentation is essentially a set of programming notes.


check-snmp-iface
----------------

check-snmp-iface is a plug-in for Nagios and compatible systems such
as Icinga.

It is designed for efficient polling of all the interfaces of a large
ISP. Where efficiency is allowing a single Nagios server to poll all
interfaces, and minimising the load on the management plane of the
routers.


Indended Usage
--------------

    check-snmp-iface -h HOSTNAME -a ADDRESS -i INTERFACE-NAME [-v]

*-h _HOSTNAME_*

_Router to check._ You must be careful to always use the same name
for the same host. This name is not resolved through DNS. It is used
in the Redis database to identify the host.

*-a _ADDRESS_*

An IPv4 or IPv6 address. For a router, its control plan (Loopback0,
lo.0) address or its management address (Mgnt0, fxp0), depending how
you do SNMP.

*-i _INTERFACE-NAME_*

_Textual name of the interface to check_. The format varies by
manufacturer.

*-v*

Verbose. This activates the debugging mode, and the script is intended
to be called from the command line, not from Nagios.

*Where are the other arguments?*

You are expected to alter the script to add your own community values
and other information which does not change between calls. We're
trying to minimise argument scanning overheads.

You must use version 2 or three of the SNMP protocol. Version 2 with
communities is acceptable. To work efficiently the GETBULK command is
used, and this is not available in SNMP version 1.


Install dependency -- Redis
---------------------------

To install Redis on Debian:

    debian-8$ sudo apt-get install redis-server redis-tools python-redis
    debian-8$ sudo apt-get install python-pysnmp4 python-pysnmp4-doc python-pyasn1

To install Redis on Fedora:

    fedora-22$ sudo dnf install redis python-redis
    fedora-22$ sudo dnf install pysnmp python-pyasn1

Redis is used entirely as a soft-state cache. This allows operators to
simply FLUSHALL the contents of the Redis database to recover from
issues. Subsequent normal operation will repopulate the cache.

As a result I suggest running a Redis instance especially for this
plugin, and configuring it with:

* No "save" clauses to create RDB snapshots.

* "appendonly no" clause to suppress AOF transaction logging.

* "maxmemory-policy noeviction" as every key created by the plugin
  has an expiry explicitly set.

Leave the publication/subscription operating. The plugin uses those to
prevent a "thundering herd" when Nagios launches a few hundred plugins
to query the interfaces in a large router. One plugin will proceed to
SNMP query the router and populate the cache, the other plugins will
have subscribed to those results appearing in the cache.

TODO: Collect capacity planning guidance. Measure Redis memory use on
a 64-bit platform: (a) at idle, (b) per additional 1,000 interfaces,
(c) per additional 100 routers.


Install dependency -- Redlock
-----------------------------

I may use the  [Redlock](http://redis.io/topics/distlock) locking
algorithm if pub/sub proves unworkable to prevent "thundering herds"
of plugins launched by Nagios.

    $ git clone https://github.com/SPSCommerce/redlock-py.git

To install redlock-py on Debian:

    debian-8$ sudo apt-get install python-stdeb
    debian-8$ cd redlock-py
    debian-8$ python setup.py --command-packages=stdeb.command debianize
    debian-8$ cat <<EOF > debian/copyright
    Format: http://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
    Upstream-Name: SPS Commerce
    Upstream-Contact: Paul DeCoursey <https://github.com/optimuspaul>
    Source: https://github.com/SPSCommerce/redlock-py
    Disclaimer: Not part of Debian

    Files: *
    Copyright: 2014-2015 SPS Commerce, Inc
    License: MIT
    EOF
    debian-8$ python setup.py --command-packages=stdeb.command bdist_deb
    debian-8$ sudo dpkg -i deb_dist/python-redlock-py_1.0.5-1_all.deb


Install dependency -- PySNMP
----------------------------

PySNMP can walk an entire table into Python with little fuss. It can
use SNMPv2c and BULKGET, and so is efficient.

    debian-8$ sudo apt-get install python-pysnmp4 python-pyasn1

    fedora-22$ sudo dnf install pysnmp python-pyasn1


Target configuration
--------------------

Cisco IOS. Configure:

    access-list 99 remark Allow SNMP access from these addresses
    access-list 99 permit 192.0.2.0 0.0.0.255

    ipv6 access-list SNMP-LIST6
     remark Allow SNMP access from these addresses
     permit 2001:db8::/32

    snmp-server community PwQo3s49lGpX5qF3 RO ipv6 SNMP-LIST6 99
    snmp-server contact Aunt Ada <ada.doom@example.org>
    snmp-server location Behind the woodshed, Cold Comfort Farm

Juniper JUNOS. Configure:

    snmp {
        contact "Aunt Ada <ada.doom@example.org>";
        location "Behind the woodshed, Cold Comfort Farm";
        community PwQo3s49lGpX5qF3 {
            authorization read-only;
            clients {
                192.0.2.0/24;
                2001:db8::/32;
            }
        }
    }

Net-SMNP. Alter /etc/snmp/snmpd.conf

    agentAddress udp:161,udp6:161
    rocommunity PwQo3s49lGpX5qF3 192.0.2.0/24
    rocommunity6 PwQo3s49lGpX5qF3 2001:db8::/32
    sysLocation Behind the woodshed, Cold Comfort Farm
    sysContact Aunt Ada <ada.doom@example.org>


Nagios
------

This is a Nagios plugin, following the [specification](http://nagios.sourceforge.net/docs/3_0/pluginapi.html).

CRITICAL events

* A failure to retrieve sysUptTime: the first SNMP query sent, and
  required to be implemented.

* Administratively up, operationally down.

* Receive CRC errors on ethernet interfaces. This implies collecting
  the etherLike MIB, but that would be worthwhile for this feature
  alone.

* Sustained discards

* Very low or high utilisation

WARNING events

* Interface flap in past five minutes, currently Up.

* Low or high utilisation.

* Multicast traffic is more than 50% of link capacity.

* CRC count has increased.

* Interface counter discontinuity, this usually indicates a card
  replacement.

UNKNOWN events

* A failure to retrieve ifIndex after successfully GETing sysUpTime.


Redis schema -- ifTable:_HOSTNAME_:_INTERFACE_:_SYSUPTIME_
----------------------------------------------------------

These keys store the results of ifTable and ifXTable in a dictionary hash.

The following are from system:

 * sysUpTime

The following are from ifTable:

 * ifIndex, ifDescr, ifType, ifMtu, ifSpeed, ifPhysAddress,
   ifAdminStatus, ifOperStatus, ifLastChange, ifInOctets,
   ifInUcastPkts, ifInNUcastPkts, ifInDiscards, ifInErrors,
   ifInUnknownProtos, ifOutOctets, ifOutUcastPkts, ifOutNUcastPkts,
   ifOutDiscards, ifOutErrors, ifOutQLen, ifSpecific

The following are from ifXTable:

 * ifName, ifInMulticastPkts, ifInBroadcastPkts, ifOutMulticastPkts,
   ifOutBroadcastPkts, ifHCInOctets, ifHCInUcastPkts,
   ifHCInMulticastPkts, ifHCInBroadcastPkts, ifHCOutOctets,
   ifHCOutUcastPkts, ifHCOutMulticastPkts, ifHCOutBroadcastPkts,
   ifLinkUpDownTrapEnable, ifHighSpeed, ifPromiscuousMode,
   ifConnectorPresent, ifAlias, ifCounterDiscontinuityTime'

Derived from these are some convenience values:

* sysuptime_text -- sysuptime in days, hours, minutes, seconds and as
  an estimate of the UTC date and time when the host came up

* ifname_key -- the best available name for the interface. It does not
  contain whitespace.

* description_text -- the best available interface description

* in_octets -- ifHCInOctets if it exists, otherwise ifInOctets

* out_octets -- similarly

* in_ucast_pkts -- ifHCInUcastPkts if exists, otherwise ifInUcastPkts

* out_ucast_pkts -- similarly

* in_pkts -- (ifHCInUcastPkts + ifHCInMulticastPkts +
  ifHCInBroadcastPkts) if they all exist, otherwise (ifInUcastPkts,
  ifInNUcastPkts). 32-bit and 64-bit values are not mixed, too allow
  wrap-around detection.

* out_pkts -- similarly

* hc_flag -- high capacity counters exist, used for wrap_around
  calculations.

* speed_mbps -- ifHighSpeed if it exists, otherwise max(int(ifSpeed /
  1000), 1). This means the special value 0 still means that the speed
  is unknown, the value 1 means (0bps < speed <= 1Mbps), and the other
  values are analogous to ifHighSpeed.

The following are created for performance monitoring and debugging:

* row_create_utc, start_snmp_utc, end_snmp_utc

* snmp_address

* hostname_key, ifname_key, ifindex_key, expire_secs


Tweaks
------

How should we handle differences in SNMP implementation. A lot of
Nagios plugins have flags, surely we can do better than that.

A strategy would seem to be to retrieve system.sysDescr and pass it
through to a module which contains the knowledge of differences
between SNMP. That module can then return a list which sets flags in
Redis for use by clients of the cache.

Centralising determining the tweak in the cache rather than in the
client seems to make some sense.

The Redis key "tweak:_HOSTNAME_" set can contain:

* ignore-frametoolongs -- set on Cisco 6500/7200-series switches.

Some sample sysDescr

    Juniper Networks, Inc. m320 internet router, kernel JUNOS 10.4R8.6 #0: 2013-01-05 10:22:53 UTC     builder@faranth.juniper.net:/volume/build/junos/10.4/release/10.4R8.6/obj-i386/bsd/sys/compile/JUNIPER Build date: 2013-01-05 09:37:36 UTC Copyright (c) 19

    Juniper Networks, Inc. mx480 internet router, kernel JUNOS 13.3R4-S4, Build date: 2015-01-09 11:25:50 UTC Copyright (c) 1996-2015 Juniper Networks, Inc.

    Juniper Networks, Inc. ex4550-32f Ethernet Switch, kernel JUNOS 12.3R6.6, Build date: 2014-03-13 08:35:12 UTC Copyright (c) 1996-2014 Juniper Networks, Inc.

    Cisco IOS Software, s72033_rp Software
    (s72033_rp-ADVIPSERVICESK9-M), Version 12.2(33)SRC2, RELEASE
    SOFTWARE (fc2)
    Technical Support: http://www.cisco.com/techsupport
    Copyright (c) 1986-2008 by Cisco Systems, Inc.
    Compiled Thu 18-Sep-08 12:37 by prod_r

    Cisco IOS Software, 7300 Software (C7300-K91P-M), Version 12.2(25)S14, RELEASE SOFTWARE (fc2)
    Technical Support: http://www.cisco.com/techsupport
    Copyright (c) 1986-2007 by Cisco Systems, Inc.
    Compiled Thu 23-Aug-07 11:49 by tinhuang


Copyright and license
---------------------

Copyright © AARNet Pty Ltd (ACN  084 540 518), 2015.

At this time there is no license for further distibution.
