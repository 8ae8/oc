OpenConnect client handler
==========================

It's only a simple script to ensure that VPN connection is stable 
due to current network problems in my location
(I'm living in Iran and we have been banned for opening many websites!) :/
Anyways, Forgive me for any mistakes.   
It was only tested on my own system (ubuntu 18), 
and system of couple of my friends and it worked as well as it supposed to.


## Requirements
1. Openconnect   
   
    > To check if you have openconnect in your system, just try `openconnect`.   
    to install openconnect run `sudo apt install openconnect`
2. Python3
    
    > This script is been written in python. I tried with python 3.6


##  Steps

1. Clone script and go in directory

```bash
git clone git@github.com:saeed-kamyabi/oc.git
cd oc
```

2. Setup   
Set and store environments to load settings from for further usage.   
If you don't setup the script, It works properly with default settings.

```bash
python run.py setup
```

3. Run

```bash
python run.py
```

> server certification will be loaded automatically for data encryption.
