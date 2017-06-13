## XenMonitor

This is a rather silly tool that processes the output of the `xentop` command, 
and sends the resulting performance information to a statsd compatible endpoint.

Ideally, I'd much prefer a SNMP based system, but as far as I can find, no
such thing exists (there is something in libvirt, but I'm not using libvirt).

Dependencies:

 - [statsd]

Setup:

- The user the daemon executes as *must* be able to execute `sudo xentop`
	 *without* a password. 
- Edit `xen_monitor.py`, and update `STATSD_HOST_ADDRESS` with the address
	 of your statsd aggregator address.
- Place the `xen_monitor.py` somewhere. Currently, the init file in the
	 repository expects `/usr/local/bin/xen_monitor.py`, but you can place it
	 wherever, as long as you update the init file.
- Place the init file in `/etc/init.d/xenmonitor`. You will probably need
	 to update the `RUNAS` variable in this file (unless you too use the username
	 `durr` on your linux box).
- `sudo update-rc.d xenmonitor enable` to enable the service. `sudo service 
	 start xenmonitor` to start immediately.

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

Have Fun!

License: BSD

[statsd]: https://pypi.python.org/pypi/statsd/
