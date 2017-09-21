## AvoMonitor

This is a rather silly tool to poll a Avocent PM3000 (and probably PM2000) PDU, 
and forward the resulting power consumption metrics to a statsd instance.

Dependencies:

 - [statsd]
 - [pysnmp]

Setup:

 - Edit `avocent_power_mon.py`, and update the settings:
     - `STATSD_HOST_ADDRESS` is the address of your statsd aggregator address.
     - `PDU_DEVICE_ADDRESS` is the IP of your avocent PDU.
     - `SNMP_COMMUNITY_STRING` is your SNMP community string
 - Place the `avocent_power_mon.py` somewhere. Currently, the init file in the
 repository expects `/usr/local/bin/avocent_power_mon.py`, but you can place it
 wherever, as long as you update the init file.
 - Place the init file in `/etc/init.d/avomonitor`. You will probably need
 to update the `RUNAS` variable in this file (unless you too use the username
 `durr` on your linux box).
 - With a Sane Init system:
     - `sudo update-rc.d avomonitor enable` to enable the service. `sudo service 
       start avomonitor` to start immediately.
 - Or SystemD:
     - `sudo systemctl daemon-reload` to rescan init files

Some stats aren't forwarded, specifically `MAXMEM(k)`, `MAXMEM(%)`, `VBDS`, and 
`VBD_OO`. This is because in my application, they're constant and fixed, so I 
don't feel the need to bother. 

Due to the limitations of the statsd message format, some modifications are done to the 
string keys (parenthesis in the column names break things). Additionally, some cleaning
is done to your VM names, though this is probably less thorough then it needs to be to 
handle arbitrary VM names. Primarily, literal dots (`.`) in the VM names are transformed to
underscores (`_`), because otherwise they wind up being interpreted as components of the
statsd gauge path. Other special characters are not currently handled, their presence
will probably cause statsd to do interesting or strange things. It is probably not
a good idea to use this tool in a context where the VM names can be controlled by a
untrusted user.

The end result is some totally awesome graphs:

![alt text](https://raw.githubusercontent.com/fake-name/StatsdWidgets/master/XenStats/XenVMs.png "Grafana Graphs")

Have Fun!

License: BSD

[statsd]: https://pypi.python.org/pypi/statsd/
[pysnmp]: http://pysnmp.sourceforge.net/
