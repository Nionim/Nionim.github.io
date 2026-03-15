#!/usr/bin/env python3

#
# Я это говно писал с винды, чтобы перебежать на линь.
# Изначальная версия скрипта была на bash, частично написана нейронкой с личными вправками.
# Так что воть
# Возможно я и его потом перепишу, если он не будет меня устраивать, но пока всё нормально
#

# Разметка диска
# N - All space on the disk
# 500MiB - BOOT
# 4GiB - SWAP (Maybe i can set more but not needed)
# Main space: N - BOOT - SWAP

# I cant write it normally on Windows. But it work
# ignore type only for develop
from archinstall.lib.networking import ping # type: ignore
import getpass, os, datetime, subprocess
from datetime import datetime
from pathlib import Path

CHROOT_SCRIPT = """
#!/bin/bash

timedatectl set-timezone Europe/Moscow
ln -sf /usr/share/zoneinfo/Europe/Moscow /etc/localtime
hwclock --systohc

echo -e "{locales}" > /etc/locale.gen
locale-gen

echo "{hostname}" > /etc/hostname
cat > /etc/hosts <<EOF
127.0.0.1 localhost
::1       localhost
127.0.1.1 {hostname}.localdomain {hostname}
EOF

echo "root:{root_password}" | chpasswd
useradd -m {username}
echo "{username}:{user_password}" | chpasswd
usermod -aG wheel,audio,video,storage,optical {username}

echo "%wheel ALL=(ALL) ALL" >> /etc/sudoers

systemctl enable NetworkManager

grub-install --target=x86_64-efi --efi-directory=/boot/efi --bootloader-id=GRUB --recheck {disk}
grub-mkconfig -o /boot/grub/grub.cfg

exit
"""

# Logs file
ERRORS = "/tmp/arch_installer/errors.log"

# Needed packages
NEEDED_PACKAGES = [
    "base", "linux",
    "linux-firmware",
    "nano", "sudo", 
    "networkmanager", 
    "grub", "efibootmgr", 
    "os-prober" ]

# DeltaCion's setup
CITORY_PACKAGES = [
    "firefox", "stow", "fastfetch", "7zip" ]

# Needed locales
NEEDED_LOCALES = [
    "en_US.UTF-8 UTF-8", 
    "ru_RU.UTF-8 UTF-8", 
    "ru_UA.UTF-8 UTF-8" ]

ETHERNET_CHECKS = 0

# Only main names/passwords
def set_variables():
    global HOSTNAME, USERNAME
    global ROOT_PASSWORD, USER_PASSWORD
    
    HOSTNAME = input("Set Hostname: ")
    USERNAME = input("Set Username: ")
    ROOT_PASSWORD = getpass.getpass("Set Root-password: ")
    USER_PASSWORD = getpass.getpass("Set User-password: ")
    if not HOSTNAME or len(HOSTNAME) <= 1:
        set_this_fvking_variables("SET THE F### HOSTNAME!")
    if not USERNAME or len(USERNAME) <= 1:
        set_this_fvking_variables("SET THE F### USERNAME!")
    if not ROOT_PASSWORD or len(ROOT_PASSWORD) <= 1:
        set_this_fvking_variables("SET THE F### ROOT_PASSWORD!")
    if not USER_PASSWORD or len(USER_PASSWORD) <= 1:
        set_this_fvking_variables("SET THE F### USER_PASSWORD!")

def set_this_fvking_variables(text: str):
    print(text)
    set_variables()

# Just set a disk name
def set_disk_name():
    global DISK_NAME
    subprocess.run(["lsblk", "-d", "-o", "NAME,SIZE,TYPE"])
    DISK_NAME = "/dev/"+input("\nEnter the disk name (ex: sda): ")
    if not DISK_NAME or len(DISK_NAME) <= 1:
        print("Set a disk name!")
        set_disk_name()

# Set a partions size
def set_partions_space():
    print("U cant replace/remove partions. " \
    "\nUf u need it - Open script and rewrite it.")
    global BOOT_SPACE
    global SWAP_SPACE
    BOOT_SPACE = str(input("Print boot space (ex: +500M): ").strip() or "+500M")
    SWAP_SPACE = str(input("Print swap space (ex: +4G): ").strip() or "+4G")

def run(cmd: list[str]):
    try: subprocess.run(cmd, check=True, capture_output=True)
    except subprocess.CalledProcessError as e: log_error(e)
    except Exception as e: log_error(f"Unexpected error: {str(e)}")

def use_citory_packages_or_not_lol_cool_func_name_bro():
    global NEEDED_PACKAGES
    USE_CITORY_PACKAGES = bool(input("Use citory's package list? (True|False)".strip() or False))
    if USE_CITORY_PACKAGES:
        NEEDED_PACKAGES += CITORY_PACKAGES

# Cool code i know that
def prepare_disk():
    # Formatting
    run(["wipefs", "-a", DISK_NAME])
    run(["sgdisk", "-Z", DISK_NAME])
    run(["sgdisk", "-o", DISK_NAME])

    disk_partitioning()

    # Make FS
    run(["mkfs.fat",  "-F32", f"{DISK_NAME}1"])
    run(["mkswap",    "-f",   f"{DISK_NAME}2"])
    run(["mkfs.ext4", "-F",   f"{DISK_NAME}3"])

    run(["partprobe", DISK_NAME])


def finnally_down():
    run(["mount",   f"{DISK_NAME}3", "/mnt"])
    Path("/mnt/boot/efi").mkdir(parents=True, exist_ok=True)
    run(["mount",   f"{DISK_NAME}1", "/mnt/boot/efi"])
    run(["swapon",  f"{DISK_NAME}2"])

    print("Packages installing..")
    run(["pacstrap", "/mnt"] + NEEDED_PACKAGES)

    result = subprocess.run(["genfstab", "-U", "/mnt"], capture_output=True, text=True)
    Path("/mnt/etc/fstab").write_text(result.stdout)

    dude_chroot() 
    Path("/mnt/tmp/config.sh").write_text(CHROOT_SCRIPT)
    Path("/mnt/tmp/config.sh").chmod(0o755)

    run(["arch-chroot", "/mnt", "/tmp/config.sh"])
    run(["umount", "-R", "/mnt"])

# Partioning disk (Les go install the fvking system!)
def disk_partitioning():
    print("Just do it!")
    print(f"Selectet disk: {DISK_NAME}")
    fdisk_cmd = [
        "g",                                        # GPT Table
        "n", "1", "", BOOT_SPACE, "t", "1",         # Boot
        "n", "2", "", SWAP_SPACE, "t", "2", "19",   # Swap
        "n", "3", "", "",                           # Other
        "w"                                         # Write it
    ]
    try: subprocess.run(["fdisk", DISK_NAME], input=("\n".join(fdisk_cmd) + "\n"), text=True, check=True, capture_output=True)
    except Exception as e: log_error(f"Disk partitioning failed: {e}")

# Final erorrs list
def print_errors():
    if os.path.exists(ERRORS) and os.path.getsize(ERRORS) > 0:
        with open(ERRORS, 'r', encoding='utf-8') as f:
            print(f"[ Total Errors:{len(f.readlines())} ]")
            print(f.read())
        
# For ^ that (^^^ check previus lines!!!) step
def log_error(msg: str):
    os.makedirs(os.path.dirname(ERRORS), exist_ok=True)
    with open(ERRORS, "a", encoding="utf-8") as f:
        current_time = datetime.now().strftime("%H:%M:%S")
        f.write(f"[{current_time}] {msg}\n")
        print(f"[{current_time}] {msg}")

# Чек айпишников.
# Почему несколько айпишников? 
#   - Потому что роскомпозор постоянно банит новые адреса.
def check_online():
    global ETHERNET_CHECKS
    ETHERNET_CHECKS+=1
    if ETHERNET_CHECKS >= 3: return False
    ips = ["1.1.1.1", "8.8.8.8", "google.com"]
    for ip in ips:
        try:
            ping(ip)
            return True
        except Exception as ex:
            print(f"HA! I cant check this ip {ip}!")
            print(ex)
            log_error(ex)
    return True


# Dont touch it
# Only for add more steps
def main() -> None:
    if not check_online(): 
        print("Cannot install! Connect to ethernet before run it!")
        subprocess.call("iwctl device list")
        return None
    use_citory_packages_or_not_lol_cool_func_name_bro()

    set_variables()

    set_disk_name()
    set_partions_space()

    prepare_disk()
    
    finnally_down()
    print_errors()

if __name__ == "__main__":
    main()

# Dude..
def dude_chroot():
    global CHROOT_SCRIPT
    CHROOT_SCRIPT = CHROOT_SCRIPT.format(
        locales="\\n".join(NEEDED_LOCALES), hostname=HOSTNAME,
        root_password=ROOT_PASSWORD, username=USERNAME,
        user_password=USER_PASSWORD, disk=DISK_NAME
    )
