import subprocess
import time
import os

try:
    devices = subprocess.run("lsblk", capture_output=True, text=True)
    busybox = False
    print(r"""  //SETUP// (Thanks to Lunariansia!)
Welcome to the PhlgOS installer, where we will guide you through the installation of your system.
Reminder: You can press Ctrl+C anytime to end this setup process but you will most likely be left with an unusable system.""")
    install_destination = "/dev/" + input(fr"""Which partition do you want your system installed on? WARNING: This will destroy all data in your partition. (For making more partitions, I recommend using GParted/Parted as partitioning is not supported here. It might get added in a future update.)
Partitions:
{devices.stdout}
>/dev/""")
    use_gnu_coreutils = input("Do you want to use the GNU Coreutils or Busybox? (type 1 for GNU Coreutils, or 2 for Busybox) ")
    if use_gnu_coreutils == "1":
        busybox = False
    else:
        busybox = True

    def choose_init_system():
        init = input(r"""What init system do you want to use? (0 to do the init manually, 1 to use sysvinit (default), 2 to use runit, or 3 to use OpenRC)
>""")
        inits = ["sysvinit", "runit", "openrc"]
        if init == '0':
            print("Type 'exit' to exit the bash shell.")
            os.system("bash")
        elif init == '1' or init == '2' or init == '3':
            print(f"You have chosen the init system {inits[int(init)-1]}")
        elif not init:
            print("You have chosen the init system sysvinit.")
            return "sysvinit"
        else:
            print("Invalid choice. Let's try this again.")
            choose_init_system()
        return inits[int(init)-1].lower()

    init_system = choose_init_system()
    kernels = subprocess.run("apt list --all-versions linux-image-*", capture_output=True, text=True)
    kernel_version = "linux-image-" + input(fr"""Choose your linux kernel version.
Available kernels:
{kernels.stdout}
>linux-image-""")
    shell = input(r"""In this step, you will install a shell. Name the shell, and it will be installed. Keep in mind that you must specify a valid APT package for the shell.
>apt install """)
    root_password = input(r"""Choose a root password (or leave blank for no password)
>""")
    username = input(r"""Choose a username for your user (leave blank for no user)
>""")
    if username:
        password = input(rf"""Password for {username}
>""")
    
    def ask_net_conf():
        net_conf = input(r"""In this step you will configure your internet. Type 1 to use DHCP, or type 2 to use a static IP.
>""")
        if net_conf == '1':
            return 'dhcp'
        elif net_conf == '2':
            return 'static'
        print("That isn't a valid choice. Let's try this again.")
        ask_net_conf()
    net_conf = ask_net_conf()

    def choose_bootloader():
        bootloader_prompt = input(r"""Choose your bootloader. (1 for Limine (recommended for this OS, default), 2 for GRUB.)
>""")
        if bootloader_prompt == '1':
            return 'limine'
        elif bootloader_prompt == '2':
            return 'grub'
        print("That isn't a valid choice. Let's try this again.")
        choose_bootloader()
    bootloader = choose_bootloader()

    input("Installing the graphical environment: After booting, you can install whatever graphical environment you want. For example, you could run XFCE. Or just run pure TTY.\nYou have finished every step and all that remains is the finalization. Press enter to continue.")
    print(r"""  //FINALIZATION//
This is the last step in the OS installation. You can sit back and relax, but feel free to monitor the output to check for errors.""")
    print("This system already has GNU Coreutils, so this step is skipped.\n[+] You have finished installing GNU Coreutils. (the next step is installing you init system)") if busybox is False else print("Installing Busybox")
    if busybox:
        try:
            subprocess.run("apt purge coreutils -y && apt install busybox-static -y && busybox --install -s /bin", check=True)
            print("[+] You have finished installing Busybox instead of the GNU Coreutils. (the next step is installing the init system.)")
        except subprocess.CalledProcessError as e:
            print(f"An error occurred: {e}\nThe setup has gone wrong, and your system will not be usable. But don't worry, as your partition {install_destination} has not been touched. You can fix it after this script exits.")
            exit(1)
        except Exception as e:
            print(f"An error occured: {e}. You can fix it with the shell after the program exits.")
            exit(1)
    print(f"Installing the init system {init_system}")
    if init_system == 'sysvinit':
        try:
            subprocess.run("apt install sysvinit-core -y", check=True)
            subprocess.run('apt purge systemd systemd-sysv -y', check=True)
            subprocess.run("update-alternatives --set init /lib/sysvinit/init", check=True)

            with open("/etc/default/grub", "r+") as f:
                grub = f.read()
                f.write(grub.replace("systemd", "sysvinit"))
            subprocess.run("update-grub", check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error in installing the sysvinit init system: {e}\nThe setup has gone wrong, and your system will not be usable. But don't worry, as your partition {install_destination} was not touched. You can fix your error with the shell after this setup script exits.")
            exit(1)

        except Exception as e:
            print(f"An error occurred: {e}\nYou can fix this error with the shell after the setup script exits.")
            exit(1)
    elif init_system == 'openrc':
        try:
            subprocess.run("apt install openrc -y", check=True)
            subprocess.run("update-alternatives --set-init /usr/bin/openrc-init", check=True)
            os.makedirs("/etc/runlevels/default", exist_ok=True)
            os.makedirs("/etc/runlevels/sysinit", exist_ok=True)

        except subprocess.CalledProcessError as e:
            input(f"Error in installing OpenRC: {e}\nThe setup has gone wrong, and your system will not be usable. But don't worry, as your partition {install_destination} was not touched. You can fix this error with the shell after the installation script exits.")
            exit(1)

        except Exception as e: 
            print(f"An error occurred: {e}\nYou can fix this error with the shell that will automatically run after the program exits.")
            exit(1)
    elif init_system == 'runit':
        try:
            subprocess.run("apt install runit-init -y", check=True)
            subprocess.run("update-alternatives --set init /usr/bin/runit-init", check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error in installing runit: {e}\nThe setup has gone wrong, and your system will not be usable. But don't worry, as your partition {install_destination} was not touched. You can fix this error after the program exits using the shell.")
            exit(1)
    print(f"[+] You have finished installing the init system! You will move on to the next step. (installing your linux image which is {kernel_version})")
    try:
        subprocess.run(f"apt install {kernel_version} -y", check=True)
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}\nYou can fix this error with the shell that will appear after the program exits.")
        exit(1)
    except Exception as e:
        print(f"An error occurred: {e}\nYou can fix this error with the shell that will appear after the program exits.")
        exit(1)
    print(f"[+] You have finished installing the kernel! You will move on to the next step. (installing your shell which is {shell})")
    print(f"Installing the {shell} shell. If the installation fails, then it's probably because you picked a non-existent shell outside the repos of APT.")
    try:
        subprocess.run(f"apt install {shell}", check=True)
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}\nYou can fix this error after going to the shell, after this program exits.")
        exit(1)
    except Exception as e:
        print(f"An error occurred: {e}\nYou can fix this error in the shell after this program exits.")
        exit(1)
    
    print("[+] You have finished installing the shell! You will move on to the next step. (applying your credentials)") if root_password and username else print("[+] You have finished installing the shell! You will move on to the next step. (configuring your internet)")
    if root_password or username:
        try:
            if root_password:
                print(f"[...] Applying your root password {root_password}")
                subprocess.run(f"chpasswd root:{root_password}", check=True)
                print(f"[+] You have applied your root password {root_password}!")
            if username:
                print(f"[...] Making a new user with username {username}")
                subprocess.run(f"useradd -m -s /bin/{shell} {username}", check=True)
                print(f"[+] Done making a user with username {username}! You will apply the user's password now.") if password else print(f"[+] Done making a user with username {username}!")
                if password:
                    print(f"[...] Making a password for the user {username} (password: {password})")
                    subprocess.run(f"chpasswd {username}:{password}")
        except subprocess.CalledProcessError as e:
            print(f"An error occurred: {e}\nYou can fix this error with the shell after the program exits.")
            exit(1)
        except Exception as e:
            print(f"An error occurred: {e}\nYou can fix this error with the shell after the program exits.")
            exit(1)
    
    print()

except KeyboardInterrupt:
    subprocess.run("clear")
    print("Exiting...")
    time.sleep(2)
    exit(130)
    
except Exception as e:
    input(f"An unexpected error occured: {e}\nYou can press any key to exit (you can fix the error in the shell after this program exits).")
    exit(1)
