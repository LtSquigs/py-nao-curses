NAO Nethack Python-Curses Client
===========================================

This is a simple curses client that allows one ot play nethack on the NAO server with a few extra features.

Features
--------

### Completed
* In Nethack, clicking on spots will give information on the spots based off tiles, similar to far look (;)
### Planned
* Seperating Nethack information into windows based off vt\_tiledata

Installation
------------

In order to use this client, you must be running some form of nix (as it relies on curses).

In order to install just grab the repo:
	git clone git@github.com:LtSquigs/py-nao-curses.git

Then run the main python file
	python main.py

Usage
-----
	python main.py

Debugging
---------

Various information can be recorded in a file called 'debug' by setting the debug level to more than 0 in main.py


