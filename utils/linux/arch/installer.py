#!/usr/bin/env python3

#
# Я это говно писал с винды, чтобы перебежать на линь.
# Изначальная версия скрипта была на bash, частично написана нейронкой с личными вправками.
# Так что воть
# Возможно я и его потом перепишу, если он не будет меня устраивать, но пока всё нормально
#

from archinstall.lib.networking import ping # type: ignore
import getpass, os, datetime, subprocess, sys

# Logs file
ERRORS = "/tmp/arch_installer/errors.log"

# Needed packages
NEEDED_PACKAGES = [
    "base", "linux",
    "linux-firmware",
    "nano", "sudo", 
    "networkmanager", 
    "grub", "efibootmgr", 
    "os-prober"
]

# DeltaCion's setup
CITORY_PACKAGES = NEEDED_PACKAGES + [
    "firefox", "stow"
]

# Needed locales
NEEDED_LOCALES = [
    "en_US.UTF-8 UTF-8", 
    "ru_RU.UTF-8 UTF-8", 
    "ru_UA.UTF-8 UTF-8"
]

ETHERNET_CHECKS = 0

def set_variables():
    global HOSTNAME, USERNAME
    global ROOT_PASSWORD, USER_PASSWORD
    
    HOSTNAME = input("Set Hostname: ")
    USERNAME = input("Set Username: ")
    ROOT_PASSWORD = getpass.getpass("Set Root-password: ")
    USER_PASSWORD = getpass.getpass("Set User-password: ")

def print_errors():
    if os.path.exists(ERRORS) and os.path.getsize(ERRORS) > 0:
        with open(ERRORS, 'r', encoding='utf-8') as f:
            print(f"[ Total Errors:{len(f.readlines())} ]")
            print(f.read())
        
def log_error(e: str):
    os.makedirs(os.path.dirname(ERRORS), exist_ok=True)
    with open(ERRORS, "a", encoding="utf-8") as f:
        current_time = datetime.now().strftime("%H:%M:%S")
        f.write(f"[{current_time}] {e}\n")

def check_online(ip: str = "1.1.1.1"):
    global ETHERNET_CHECKS
    ETHERNET_CHECKS+=1
    if ETHERNET_CHECKS >= 3: return False
    try:
        ping(ip)
    except Exception as ex:
        if ip != "8.8.8.8" and check_online("8.8.8.8"): return True
        if ip != "google.com" and check_online("google.com"): return True
        print(f"HA! I cant check this ip {ip}!")
        print(ex)
        log_error(ex)
        return None
    return True


def main() -> None:
    if not check_online("1.1.1.1"): 
        print("Cannot install! Connect to ethernet before run it!")
        subprocess.call("iwctl device list")
        return None
    
    set_variables()
    print_errors()

if __name__ == "__main__":
    main()
