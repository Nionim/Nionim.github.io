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
import getpass
import os
import subprocess
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
127.0.0.1       localhost
::1             localhost
127.0.1.1       {hostname}.localdomain {hostname}
EOF
echo "root:{root_password}" | chpasswd
useradd -m -G wheel,audio,video,storage,optical {username}
echo "{username}:{user_password}" | chpasswd
echo "%wheel ALL=(ALL) ALL" >> /etc/sudoers
systemctl enable NetworkManager
grub-install --target=x86_64-efi --efi-directory=/boot/efi --bootloader-id=GRUB --recheck {disk}
grub-mkconfig -o /boot/grub/grub.cfg
{aur_install_script}
exit
"""

# Logs file
ERRORS = "/tmp/arch_installer/errors.log"

# Live Logs
LIVE_LOGS = True

# Needed packages
NEEDED_PACKAGES = [
    "base", "linux",
    "linux-firmware",
    "nano", "sudo",
    "networkmanager",
    "grub", "efibootmgr",
    "os-prober", "base-devel"
]

# DeltaCion's setup
CITORY_PACKAGES = [
    "firefox", "stow", "fastfetch", "7zip", "otf-font-awesome"
]

# Needed locales
NEEDED_LOCALES = [
    "en_US.UTF-8 UTF-8",
    "ru_RU.UTF-8 UTF-8",
    "ru_UA.UTF-8 UTF-8"
]

INSTALL_AUR = False
INSTALL_AUR_PACKAGES = False
AUR_SCRIPT = ""
AUR_PACKAGES = [
    "desktopify-lite"
]

def build_aur_script(install_aur, install_aur_packages):
    global AUR_SCRIPT
    if not install_aur:
        return
    AUR_SCRIPT = """
		pacman -S --needed --noconfirm git base-devel
		git clone https://aur.archlinux.org/yay.git
		cd yay && makepkg -si --noconfirm
	"""
    if install_aur_packages:
        AUR_SCRIPT += f"\nyay -S --needed --noconfirm {' '.join(AUR_PACKAGES)}"

def say_me_aur():
    global INSTALL_AUR
    global INSTALL_AUR_PACKAGES
    inp = input("Install AUR (With yay)? (True|False): ").strip().lower()
    INSTALL_AUR = inp in ('true', 't', 'yes', 'y', '1')
    inp = input("Install AUR packages? (True|False): ").strip().lower()
    INSTALL_AUR_PACKAGES = inp in ('true', 't', 'yes', 'y', '1')

def set_variables():
    global HOSTNAME, USERNAME, ROOT_PASSWORD, USER_PASSWORD

    HOSTNAME = input("Set Hostname: ").strip()
    USERNAME = input("Set Username: ").strip()
    ROOT_PASSWORD = getpass.getpass("Set Root-password: ")
    USER_PASSWORD = getpass.getpass("Set User-password: ")

    if not HOSTNAME:
        print("SET THE F### HOSTNAME!")
        set_variables(); return
    if not USERNAME:
        print("SET THE F### USERNAME!")
        set_variables(); return
    if not ROOT_PASSWORD:
        print("SET THE F### ROOT_PASSWORD!")
        set_variables(); return
    if not USER_PASSWORD:
        print("SET THE F### USER_PASSWORD!")
        set_variables(); return

def set_disk_name():
    global DISK_NAME
    subprocess.run(["lsblk", "-d", "-o", "NAME,SIZE,TYPE"])
    disk = input("\nEnter the disk name (ex: sda): ").strip()
    if not disk:
        print("Set a disk name!")
        set_disk_name(); return
    DISK_NAME = f"/dev/{disk}"

def set_partions_space():
    print("U cant replace/remove partions. " \
          "\nIf u need it - Open script and rewrite it.")
    global BOOT_SPACE, SWAP_SPACE
    BOOT_SPACE = input("Print boot space (ex: +500M): ").strip() or "+500M"
    SWAP_SPACE = input("Print swap space (ex: +4G): ").strip() or "+4G"

def run(cmd: list[str]):
	if LIVE_LOGS:
		command = " ".join(cmd)
		print(f"Run: {command}")
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        log_error(f"Command failed: {' '.join(cmd)}\n{e.stderr}")
    except Exception as e:
        log_error(f"Unexpected error running {' '.join(cmd)}: {str(e)}")

def use_citory_packages_or_not_lol_cool_func_name_bro():
    global NEEDED_PACKAGES
    inp = input("Use citory's package list? (True|False): ").strip().lower()
    use_citory = inp in ('true', 't', 'yes', 'y', '1')
    if use_citory:
        NEEDED_PACKAGES += CITORY_PACKAGES

def prepare_disk():
    # Formatting
    run(["wipefs", "-a", DISK_NAME])
    run(["sgdisk", "-Z", DISK_NAME])
    run(["sgdisk", "-o", DISK_NAME])
    disk_partitioning()
    # Make FS
    run(["mkfs.fat", "-F32", f"{DISK_NAME}1"])
    run(["mkswap", f"{DISK_NAME}2"])
    run(["mkfs.ext4", "-F", f"{DISK_NAME}3"])
    run(["partprobe", DISK_NAME])

def dude_chroot():
    global CHROOT_SCRIPT
    CHROOT_SCRIPT = CHROOT_SCRIPT.format(
        locales="\n".join(NEEDED_LOCALES),
        hostname=HOSTNAME,
        root_password=ROOT_PASSWORD,
        username=USERNAME,
        user_password=USER_PASSWORD,
        disk=DISK_NAME,
        aur_install_script=AUR_SCRIPT
    )

def finnally_down():
    run(["mount", f"{DISK_NAME}3", "/mnt"])
    Path("/mnt/boot/efi").mkdir(parents=True, exist_ok=True)
    run(["mount", f"{DISK_NAME}1", "/mnt/boot/efi"])
    run(["swapon", f"{DISK_NAME}2"])

    keys_refresh()
    run(["pacstrap", "/mnt"] + NEEDED_PACKAGES)

    result = subprocess.run(["genfstab", "-U", "/mnt"], capture_output=True, text=True)
    if result.returncode == 0: Path("/mnt/etc/fstab").write_text(result.stdout)
    else: log_error(f"genfstab failed:\n{result.stderr}")

    dude_chroot()

    Path("/mnt/tmp").mkdir(parents=True, exist_ok=True)
    config_path = Path("/mnt/tmp/config.sh")
    config_path.write_text(CHROOT_SCRIPT.replace("\r", ""))
    config_path.chmod(0o755)
	
	run(["mkdir", "-p", "/mnt/proc"])
    run(["mkdir", "-p", "/mnt/sys"])
    run(["mkdir", "-p", "/mnt/dev"])
    run(["mkdir", "-p", "/mnt/run"])

    run(["mount", "-t", "proc", "proc", "/mnt/proc"])
    run(["mount", "--rbind", "/sys", "/mnt/sys"])
    run(["mount", "--rbind", "/dev", "/mnt/dev"])
    run(["mount", "--rbind", "/run", "/mnt/run"])

    run(["mount", "--make-rslave", "/mnt/sys"])
    run(["mount", "--make-rslave", "/mnt/dev"])
    run(["mount", "--make-rslave", "/mnt/run"])

    result = subprocess.run(["arch-chroot", "/mnt", "/tmp/config.sh"])
    if result.returncode != 0: log_error(f"arch-chroot failed with code {result.returncode}")
    run(["umount", "-R", "/mnt"])
	
def disk_partitioning():
    print("Just do it!")
    print(f"Selected disk: {DISK_NAME}")
    run(["sgdisk", "-n", f"1:0:{BOOT_SPACE}", "-t", "1:ef00", DISK_NAME])
    run(["sgdisk", "-n", f"2:0:{SWAP_SPACE}", "-t", "2:8200", DISK_NAME])
    run(["sgdisk", "-n", "3:0:0", "-t", "3:8300", DISK_NAME])
    run(["partprobe", DISK_NAME])

def print_errors():
    if os.path.exists(ERRORS) and os.path.getsize(ERRORS) > 0:
        with open(ERRORS, encoding='utf-8') as f:
            lines = f.readlines()
            print(f"[ Total Errors: {len(lines)} ]")
            print(''.join(lines))

def log_error(msg: str):
    os.makedirs(os.path.dirname(ERRORS), exist_ok=True)
    with open(ERRORS, "a", encoding="utf-8") as f:
        current_time = datetime.now().strftime("%H:%M:%S")
        f.write(f"[{current_time}] {msg}\n")
        print(f"[{current_time}] {msg}")

def keys_refresh():
    run(["pacman", "-Sy", "--noconfirm", "archlinux-keyring"])
    run(["pacman", "-Scc", "--noconfirm"])

def main() -> None:
    use_citory_packages_or_not_lol_cool_func_name_bro()
    say_me_aur()
    build_aur_script(INSTALL_AUR, INSTALL_AUR_PACKAGES)
    set_variables()
    set_disk_name()
    set_partions_space()
    prepare_disk()
    finnally_down()
    print_errors()

if __name__ == "__main__":
    main()
