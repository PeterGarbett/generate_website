

This repository is intended to be used with files
emitted by the intrusion.py image format.

Copy images from one directory as they appear in it
Place them on a directory intended to host a website
At carefully chosen intervals regenerate the index.html etc
using imageindex to produce the index.html etc
The latter operation is expensive and we avoid doing it
too frequently and when files are still moving

Converted to run using virtualvenv ; finally prompted
to do this so I can use inotify via pip on Debian.

Various problems to solve to do this including
ensuring pip is correct and removing the #! reference 
to the system python ( python3 -m ensurepip --default-pip fixes the former)

Now runs as user embed who I've generated as a normal user for
the sake of having a home directory to put this in.

