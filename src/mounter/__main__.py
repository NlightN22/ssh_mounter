#!/usr/bin/python3
from system_runner import Runner
from logger import Logger
import re
import os
import argparse
import subprocess

runner = Runner()
logger = Logger()

path_pattern = r"^((~?/?|(\./)?)([a-zA-Z0-9_.\-]+/?)+)$"

scriptname="ssh_mount_helper"

def init_logger(log_path):
    global logger
    global runner
    logger = Logger(log_path)
    runner = Runner(logger)

def input_username():
    user = input("Enter remote username: ").strip()
    while not validate_input(user):
        print("Invalid input. Please enter a valid username.")
        user = input("Enter remote username: ").strip()
    return user

def input_host(message, pattern):
    host = input(message).strip()
    while not validate_input(host, pattern):
        print("Invalid input. Please enter a valid host.")
        host = input(message).strip()
    return host

def input_path(message, pattern):
    path = input(message).strip()
    while not validate_input(path, pattern):
        print("Invalid path. Please enter a valid path.")
        path = input(message).strip()
    return path

def validate_input(value, pattern=None):
    if not value:
        return False

    if pattern and not re.match(pattern, value):
        return False

    return True

def check_and_create_directory(path):
    if not os.path.exists(path):
        response = input(f"Directory '{path}' does not exist. Would you like to create it? (yes/no): ").strip().lower()
        if response == 'yes':
            try:
                os.makedirs(path)
                logger.log(f"Directory '{path}' created successfully!")
            except Exception as e:
                logger.error(f"Error creating directory '{path}': {e}")
                exit(1)
        else:
            logger.error(f"Local mount directory '{path}' was not created.")
            exit(1)

def is_package_installed(package):
    try:
        package_installed = runner.run(f"which {package}", silent=True)
        if package_installed == 0: 
            return True
        else:
            return False
    except Exception as e:
        logger.error(f"Error during check {package} installed.")
        exit(1)

def mount_sshfs(args):
    if args.ssh_key_path:
        cmd = f"sshfs -o IdentityFile={args.ssh_key_path} {args.username}@{args.servername}:{args.remote_path} {args.local_path}"
    else:
        cmd = f"sshfs {args.username}@{args.servername}:{args.remote_path} {args.local_path}"

    try:
        result_mount = runner.run(cmd)
        if result_mount == 0:
            logger.log(f"Mounted {args.username}@{args.servername}:{args.remote_path} to {args.local_path}")
        else:
            logger.error(f"Not mounted {args.username}@{args.servername}:{args.remote_path} to {args.local_path}")
            exit(1)
    except Exception as e:
        logger.error("Error during mounting. Please ensure sshfs is installed and SSH keys are set up correctly.")
        exit(1)

def test_ssh_connection(args):
    if args.ssh_key_path:
        cmd = f'ssh -o BatchMode=yes {args.username}@{args.servername} -i {args.ssh_key_path} exit'
    else:
        cmd = f'ssh -o BatchMode=yes {args.username}@{args.servername} exit'
    try:
        result_ssh = runner.run(cmd)
        if result_ssh == 0:
            return True
        else:
            return False
    except Exception as e:
        logger.error("Error during test ssh connection. Please ensure ssh is installed and SSH keys are set up correctly.")
        exit(1)

def validate_args(args, parser):

    if args.log_path:
        validate = validate_input(args.log_path, path_pattern)
        if not validate:
            display_error_with_args("Invalid log path", args, parser)
            exit(1)
        init_logger(args.log_path)

    if not args.username and not args.quiet_mode:
        args.username = input_username()
    else:
        validate = validate_input(args.username)
        if not validate:
            display_error_with_args("Invalid username", args, parser)
            exit(1)

    host_pattern = (r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$|"
        r"(?:(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,6}\.?|[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)$")
    if not args.servername and not args.quiet_mode:
        args.servername = input_host("Enter remote host (e.g. cloud.server.com or 192.168.0.20): ", host_pattern)
    else: 
        validate = validate_input(args.servername, host_pattern)
        if not validate:
            display_error_with_args("Invalid hostname or IP address", args, parser)
            exit(1)
    if not args.remote_path and not args.quiet_mode:
        args.remote_path = input_path(f"Enter remote path (e.g. /home/{args.username}): ", path_pattern)
    else:
        validate = validate_input(args.remote_path, path_pattern)
        if not validate:
            display_error_with_args("Invalid remote path", args, parser)
            exit(1)
    if not args.local_path and not args.quiet_mode:
        args.local_path = input_path("Enter local mounting path (e.g. /mnt/keystore): ", path_pattern)
    else:
        validate = validate_input(args.local_path, path_pattern)
        if not validate:
            display_error_with_args("Invalid local path", args, parser)
            exit(1)
    check_and_create_directory(args.local_path)

    if check_mounted_path(args):
        remote_device = f'{args.username}@{args.servername}:{args.remote_path}'
        logger.log(f"{remote_device} already mounted to {args.local_path}")
        exit(1)

    if not args.ssh_key_path and not args.quiet_mode:
        use_local_key = input("Do you have local SSH keyfile for connect without password or default public key? (yes/no): ").strip().lower()
        if use_local_key == 'yes':
            args.ssh_key_path = input_path(f"Enter local key file path (e.g. ~/.ssh/{args.username}): ", path_pattern)
        else:
            create_and_install_ssh_key(args)
    
def display_error_with_args(error_message, args, parser):
    """
    Display an error message with all provided arguments.

    :param error_message: The main error message to display.
    :param args: The argparse.Namespace object containing all arguments.
    """
    print(f"ERROR: {error_message}\n")
    print("Provided arguments:")
    for arg, value in vars(args).items():
        print(f"  - {arg}: {value}")
    if parser: 
        print('')
        parser.print_help()

def is_path_mounted(local_path, remote_path):
    """
    Check if at mount path somthing already mounted

    Args:
        local_path (str): local mount point
        remote_path (str): remote device
    
    Returns:
        already_mounted: local mount point and remote is True
        busy: local mount point busy by another device
        not_mounted: local mount point free for mount
    """
    try:
        with open("/proc/mounts", "r") as f:
            mounts = f.readlines()
        for mount in mounts:
            parts = mount.split()
            mounted_path = parts[1]
            mounted_device = parts[0]
            if mounted_path == local_path:
                if remote_path in mounted_device:
                    return 'already_mounted'
                else:
                    return 'busy'
        return 'not_mounted'
    except Exception as e:
        logger.error(f"Error checking mount status: {e}")
        exit(1)

def create_and_install_ssh_key(args):
    args.ssh_key_path = create_ssh_key(args)
    if args.ssh_key_path:
        install_key_to_server(args)
        if not test_ssh_connection(args):
            logger.error("Error during test ssh connection. Check connection or setup private and public key to remote server")
            exit(1)
    
def create_ssh_key(args):
    create_ssh_key = input("Would you like to create local SSH keyfile for connect without password? (yes/no, default yes): ").strip().lower()
    if create_ssh_key == 'yes' or create_ssh_key == '':
        keypath = '~/.ssh/id_rsa'
        new_keypath = input(f"Input key path and name? (e.g. ~/.ssh/{args.username}, default: {keypath}): ").strip()
        if not new_keypath: new_keypath = keypath
        while not validate_input(new_keypath, path_pattern): 
            new_keypath = input(f"Input key path and name? (e.g. ~/.ssh/{args.username}, default: {keypath}): ").strip()
            if not new_keypath: new_keypath = keypath
        try:
            if new_keypath: keypath = new_keypath
            cmd = f'ssh-keygen -f {keypath} -q -P ""'
            create_result = runner.run(cmd)
            if create_result == 0:
                logger.log(f'Created keyfile at {keypath}')
                return keypath
            else:
                logger.error(f'Error while create keyfile at {keypath}')
                exit(1)
        except Exception as e:
            logger.error(f'Error while create SSH keyfile')
            exit(1)
    else:
        logger.error("Create and setup private and public key for connect to remote server without password")
        exit(1)

def one_choose(choices):
    for i, choice in enumerate(choices, 1):
        print(f"{i}. {choice}")

    while True:
        try:
            selection = int(input("Enter your choice (number): "))
            if 1 <= selection <= len(choices):
                return choices[selection-1]
            else:
                print("Invalid choice. Please select again.")
        except ValueError:
            print("Please enter a number.")


def error_file_not_exist(file):
    logger.error(f"File {file} does not exist.")
    exit(1)


def install_key_to_server(args):
    def error_install():
        logger.error(f'Error while install keyfile {args.ssh_key_path} to {args.username}@{args.servername}')
        exit(1)

    cmd = f'ssh-copy-id -i {args.ssh_key_path}.pub {args.username}@{args.servername}'
    try:
        install_key_result = runner.run(cmd)
        if install_key_result != 0:
            error_install()
    except Exception as e:
        error_install()


def check_mounted_path(args):
    remote_device = f'{args.username}@{args.servername}:{args.remote_path}'
    result = is_path_mounted(args.local_path, remote_device)

    if result == 'busy':
        logger.error(f"Something already mounted to {args.local_path}")
        exit(1)
    elif result == 'already_mounted':
        return True
    return False


if __name__ == "__main__":

    required_packages = [ 'ssh', 'ssh-keygen', 'sshfs', 'ssh-copy-id']
    for package in required_packages:
        if not is_package_installed(package):
            logger.error(f'Error: {package} is not installed. Please install it first. Example: apt install {package}')
            exit(1)
    
    parser = argparse.ArgumentParser(description="SSHFS mount utility")
    parser.add_argument("-u", "--username", help="Username for SSH connection")
    parser.add_argument("-s", "--servername", help="Server hostname or IP address for SSH connection")
    parser.add_argument("-r", "--remote-path", help="Remote path for mounting")
    parser.add_argument("-m", "--local-path", help="Local path for mounting")
    parser.add_argument("-k", "--ssh-key-path", help="SSH key path for connecting")
    parser.add_argument("-l", "--log-path", 
                        help='Log path, e.g. /var/log/ssh_mount_helper.log, default value "./ssh_mount_helper.log"',
                        nargs="?",
                        const="./ssh_mount_helper.log"
                        )
    parser.add_argument("-q", "--quiet-mode", action="store_true", help="Quiet mode, disable interactive mode")

    args = parser.parse_args()
    validate_args(args, parser)

    if not test_ssh_connection(args):
        if args.quiet_mode or args.ssh_key_path != '': 
            logger.error("Error during test ssh connection. Check connection or create and setup private and public key to remote server")
            exit(1)
        create_and_install_ssh_key(args)

    if not check_mounted_path(args):
        mount_sshfs(args)
    