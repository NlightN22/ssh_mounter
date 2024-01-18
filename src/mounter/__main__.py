#!/usr/bin/python3
from .system_runner import Runner
from .logger import Logger
from .sytemd_service_installer import ServiceInstaller
import re
import os
import time
import argparse
import getpass

runner = Runner()
logger = Logger()

path_pattern = r"^((~?/?|(\./)?)([a-zA-Z0-9_.\-]+/?)+)$"

scriptname="ssh_mounter"

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

def input_path(message, pattern, deafult_path = ''):
    path = input(message).strip()
    if deafult_path and not path: path = deafult_path
    while not validate_input(path, pattern):
        print(f"Invalid path: {path}. Please enter a valid path.")
        path = input(message).strip()
        if deafult_path and not path: path = deafult_path
    return path

def input_number(message, default_number = ''):
    number = input(message).strip()
    if default_number and not number: number = default_number
    while not number.isdigit():
        print(f"Invalid number: {number}. Please enter a valid path.")
        number = input(message).strip()
        if default_number and not number: number = default_number
    return number

def validate_input(value, pattern=None):
    if not value:
        return False

    if pattern and not re.match(pattern, value):
        return False

    return True

def check_and_create_directory(args):
    if not os.path.exists(os.path.expanduser(args.local_path)) and not args.quiet_mode:
        response = input(f"Directory '{args.local_path}' does not exist. Would you like to create it? (yes/no): ").strip().lower()
        if response == 'yes':
            try:
                os.makedirs(args.local_path)
                logger.log(f"Directory '{args.local_path}' created successfully!")
            except Exception as e:
                logger.error(f"Error creating directory '{args.local_path}': {e}")
                exit(1)
    if not os.path.exists(os.path.expanduser(args.local_path)):
        logger.error(f"Local mount directory '{args.local_path}' was not created.")
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

    if args.install_service and args.delete_service:
        display_error_with_args("Can't use simultaneously -i -d parameters", args, parser)
        exit(1)

    if args.install_service:
        if args.period and not args.period.isdigit(): 
            if not args.quiet_mode:
                input_number('Enter correct update period for service in seconds, e.g. 60')
            else:
                display_error_with_args("Invalid period", args, parser)
                exit(1)

    if args.log_path:
        validate = validate_input(args.log_path, path_pattern)
        if not validate:
            display_error_with_args("Invalid log path", args, parser)
            exit(1)
        init_logger(args.log_path)

    if args.quiet_mode and args.create_remote:
        display_error_with_args("Can't use simultaneously -c -q parameters", args, parser)
        exit(1)

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

def is_path_mounted(local_path):
    """
    Check if at mount path somthing already mounted

    Args:
        local_path (str): local mount point
        remote_path (str): remote device
    
    Returns:
        mounted_device or False if it is not busy
    """
    try:
        with open("/proc/mounts", "r") as f:
            mounts = f.readlines()
        for mount in mounts:
            parts = mount.split()
            mounted_path = parts[1]
            mounted_device = parts[0]
            if mounted_path == local_path:
                return mounted_device
        return False
    except Exception as e:
        logger.error(f"Error checking mount status: {e}")
        exit(1)

def input_remote_user_password(args):
    remote_user_password = getpass.getpass(f'Input remote user {args.username} password length > 4: ')
    while not remote_user_password or len(remote_user_password) < 5:
        logger.error(f'You must input remote user {args.username} password length > 4')
        remote_user_password = getpass.getpass(f'Input remote user {args.username} password length > 4: ')
    return remote_user_password

def create_remote_user(args):
    default_admin = 'root'
    remote_admin = input(f'Input remote admin username (default: {default_admin}): ').strip()
    if not remote_admin: remote_admin = default_admin

    if len(args.create_remote) < 5:
        args.create_remote = input_remote_user_password(args)

    if remote_admin == default_admin:
        cmd = f'ssh {remote_admin}@{args.servername} \'useradd -m {args.username} && echo "{args.username}:{args.create_remote}" | chpasswd && exit \''
    else:
        cmd = f'ssh {remote_admin}@{args.servername} \'sudo useradd -m {args.username} && echo "{args.username}:{args.create_remote}" | sudo chpasswd && exit \''
    try:
        result_ssh = runner.run(cmd)
        if result_ssh == 0:
            logger.log(f'User {args.username} with password {args.create_remote} successfully created at {args.servername}')
    except Exception as e:
        logger.error("Error during creating remote user. Please ensure that credentials set up correctly.")
        exit(1)

def create_and_install_ssh_key(args):
    args.ssh_key_path = create_ssh_key(args)
    if args.ssh_key_path:
        install_key_to_server(args)
    
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
    result = is_path_mounted(args.local_path)
    if not result: return False
    if remote_device in result:
        return True
    elif result:
        logger.error(f"{result} already mounted to {args.local_path}")
        exit(1)

def install_or_remove_service(args, default_service_period):
    period = args.period if args.period is not None else default_service_period
    replaced_slash = args.remote_path.replace('/', '-')
    whithout_first = replaced_slash[1:]
    service_name = f'{whithout_first}@ssh-mounter'
    installer = ServiceInstaller(quiet_mode=args.quiet_mode,external_logger=logger)

    if args.install_service:
        # current_path = os.path.dirname(os.path.abspath(__file__)) # todo delete
        # current_path = os.path.expanduser('~/.local/bin/ssh-mounter') # todo delete
        current_path = 'ssh-mounter'
        script_path = (current_path + f" -u {args.username} -s {args.servername}" +
                    f" -r {args.remote_path} -m {args.local_path} -l -p {period} -q -k {args.ssh_key_path}")
        logger.log('Prepare service...')
        service_content = installer.prepare(
            service_name=service_name,
            script_path=script_path,
            description=f'Mount remote path {args.remote_path} to local {args.local_path}',
            start_after='network.target auditd.service',
            restart_always=True,
        )
        if installer.install(service_name, service_content):
            logger.log(f'Service {service_name}.service installed successfully')
            installer.start(service_name)

    if args.delete_service:
        if installer.remove(service_name):
            logger.log(f'Service {service_name}.service removed successfully')

def main():
    default_ssh_key_path = '~/.ssh/id_rsa'
    default_log_path = f'/var/log/{scriptname}.log'
    default_service_period = 60

    required_packages = [ 'ssh', 'ssh-keygen', 'sshfs', 'ssh-copy-id']
    for package in required_packages:
        if not is_package_installed(package):
            logger.error(f'Error: {package} is not installed. Please install it first. Example: apt install {package}')
            exit(1)
    
    parser = argparse.ArgumentParser(description="SSHFS mount utility." + 
                                     "\nBase usage: ssh-mounter -u username -c StrongUserPassword -s remote-server.com -r /home/username -m /mnt/local_path -l")
    parser.add_argument("-u", "--username", help="Username for SSH connection")
    parser.add_argument("-s", "--servername", help="Server hostname or IP address for SSH connection")
    parser.add_argument("-r", "--remote-path", help="Remote path for mounting")
    parser.add_argument("-m", "--local-path", help="Local path for mounting")
    parser.add_argument("-k", "--ssh-key-path", 
                        help=f'SSH key path for connecting, default value "{default_ssh_key_path}"',
                        nargs='?',
                        default=default_ssh_key_path,
                        const=default_ssh_key_path
                        )
    parser.add_argument("-l", "--log-path", 
                        help=f'Enable log and set log path, e.g. /var/log/ssh_mount_helper.log, default path value "{default_log_path}"',
                        nargs="?",
                        const=default_log_path
                        )
    parser.add_argument("-c", "--create-remote", help="Create remote user in interactive mode. Input password for user with length > 4.")
    parser.add_argument("-q", "--quiet-mode", action="store_true", help="Quiet mode, disable interactive mode")
    parser.add_argument("-i", "--install-service", action="store_true", help="Install service for automounting remote path throught this script")
    parser.add_argument("-d", "--delete-service", action="store_true", help="Delete service for automounting remote path throught this script")
    parser.add_argument("-p", "--period", 
                        nargs="?",
                        const=default_service_period,
                        help=f"Service check period in seconds, default {default_service_period} seconds")
    
    args = parser.parse_args()
    validate_args(args, parser)

    service_install_params = True if args.install_service or args.delete_service else False

    if args.period and not service_install_params:
        period = float(args.period)
        while True:
            if not check_mounted_path(args):
                mount_sshfs(args)
            time.sleep(period)

    if service_install_params:
        install_or_remove_service(args, default_service_period)
        exit(0)

    if check_mounted_path(args):
        remote_device = f'{args.username}@{args.servername}:{args.remote_path}'
        logger.log(f"{remote_device} already mounted to {args.local_path}")
        exit(1)

    check_and_create_directory(args)

    if args.create_remote:
        create_remote_user(args)

    if not args.ssh_key_path and not args.quiet_mode:
        args.ssh_key_path = input_path("Enter local SSH key file path. File creates, if it does not existing " + 
                                    f"(e.g. ~/.ssh/{args.username}, default: {default_ssh_key_path}): ", path_pattern, default_ssh_key_path)
        if not os.path.exists(os.path.expanduser(args.ssh_key_path)):
            logger.log(f'Local SSH key file {args.ssh_key_path} does not exist')
            create_and_install_ssh_key(args)

    if not test_ssh_connection(args):
        if args.quiet_mode or args.ssh_key_path != '': 
            logger.error("Error during test ssh connection. Check connection or create and setup private and public key to remote server")
            exit(1)
        create_and_install_ssh_key(args)

    if not check_mounted_path(args):
        mount_sshfs(args)
    
    if args.install_service:
        install_or_remove_service(args, default_service_period)

if __name__ == "__main__":
    main()