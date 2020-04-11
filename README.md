OpenConnect client handler
==========================

It's only a simple script to ensure that VPN connection is stable 
due to current network problems in my location
(I'm living in Iran and we have been banned from opening many websites!) :/
Anyways, Forgive me for any mistakes.   
It was only tested on my own system (ubuntu 18), 
and system of couple of my friends and it worked as well as it supposed to.

## How it works

It's just like running openconnect command.
but with a few differences to ensure your connection is stable!
When you run the scrip:
- It runs openconnect in background and connects to VPN server.
- Pings everytime to `8.8.8.8` (sorry for that its hard coded, should be configurable in setup step :D)
- If ping time exceeded the maximum value of setting (which is configurable on setup section).
  tries 3 times, if still has the higher ping time than what is set, reconnects the VPN
- If ping time is lower than zero (usually on network problems, ping time would be -1) does the same as previous step

Just like that. it just checks the internet stability and reconnects the VPN if there is a problem.   
Sometimes when i suspend or hibernate my system. 
after a while when i come back and turn my computer on, 
I don't have to reconnect my VPN connection again, Its connected whole the time. 


## Requirements
1. Openconnect   
   
    > To check if you have openconnect in your system, just try `openconnect`.   
    to install openconnect run `sudo apt install openconnect`
2. Python3
    
    > This script is been written in python. I tried with python 3.6.   
    to install python 3.6 on ubuntu, run commands below:   
    ```
    sudo apt update
    sudo apt install python3.6
    ``` 
3. Login for openconnect VPN server
    
    > Surely you need an account of openconnect to connect to VPN server.
    As you know, its only a script to improve stability of VPN connectivity, not a VPN server :))


##  Steps

1. Clone script and go to directory

```bash
git clone git@github.com:saeed-kamyabi/oc.git
cd oc
```

2. Setup   
Set and store environments to load settings from for further usage.   
If you don't setup the script, It works properly with default settings.

```bash
python3 run.py setup
```

3. Run

```bash
python3 run.py
```

Parameters:

Parameter | Description
--- | ---
-i | selected index of profile
-p | inline system password
-y | accept question prompt

run vpn without any prompt:   
for example for profile 2 and system password of `123456` command would be:

```bash
python3 run.py -i 2 -y -p 123456
``` 

> server certification will be loaded automatically for data encryption.
