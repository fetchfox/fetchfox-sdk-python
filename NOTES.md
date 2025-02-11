I'm targeting Python 3.8, since apparently a lot of people still use it.

Kind of an arbitrary choice, and it's technically EOL, but if e.g. someone is on
Ubuntu 20.04 LTS and using the system-packaged Python, they'd be using 3.8.

Supposedly 14% of packages downloaded from PyPI were for 3.8, recently.

For `requests` I've chosen >=v2.22.0, since that happens to be what's packaged
in Ubuntu 20.04 as `python3-requests`.  Technically, Ubuntu 14.04 is still in
Legacy support, but `packages.ubuntu.com` doesn't search anything older than 20.04.

