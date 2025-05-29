# WoLControl
The goal of this repo is to establish a remote control to my local host to perform WoL (WakeOnLAn) through Telegram.

I'll use [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) API and [ether-wake](https://linux.die.net/man/8/ether-wake).

## Little trick for ether-wake
This tool need to be run as root.
To let the Telegram bot use it on your behalf I allowed `etherwake` command to be run without asking for root password.

1. Open the sudoers file using `visudo`:
   ```bash
   sudo visudo
2. Add the following line at the end (adjust the path to etherwake if necessary):
   ```bash
   <your_username> ALL=(ALL) NOPASSWD: /usr/sbin/etherwake
