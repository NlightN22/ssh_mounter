import os
import re
from .logger import Logger
from .system_runner import Runner

class ServiceInstaller():
    def __init__(self, 
                 quiet_mode: bool =False, 
                 external_logger: Logger = '',
                 external_runner: Runner = '',
                 ) -> None:
        if external_logger == '':
            self.__logger = Logger()
        else:
            self.__logger = external_logger
        if external_runner == '':
            self.__runner = Runner()
        else:
            self.__runner = external_logger
        self._path_pattern = r"^/([a-zA-Z0-9_.\-]+/?)+$"
        self._quiet_mode = quiet_mode

    def _input_path(self, message, pattern, deafult_path = '', left_part=False):
        path = input(message)
        if left_part: left_path = path.split(' ')[0]
        left_path = left_path.strip()
        if left_part: deafult_path = deafult_path.split(' ')[0]
        if deafult_path and not left_path: left_path = deafult_path
        while not self._validate_input(left_path, pattern):
            print(f"Invalid path: {path}. Please enter a valid path.")
            path = input(message)
            if left_part: left_path = path.split(' ')[0]
            left_path = path.strip()
            if deafult_path and not path: left_path = deafult_path
        return path

    def _validate_input(self, value, pattern=None):
        if not value:
            return False

        if pattern and not re.match(pattern, value):
            return False
        return True

    def _validate_path(self, script_path: str):
        left_path = script_path.split(' ')[0]
        validate_path_result = self._validate_input(left_path, self._path_pattern)
        if not validate_path_result and not self._quiet_mode:
            self.__logger.error(f'Script path {script_path} not correct')
            script_path = self._input_path(f'Please input valid script path, e.g. "/root/.local/bin/service_name arg1 arg2 arg3..."', self._path_pattern)
        elif not validate_path_result:
            self.__logger.error(f'Not correct script path {script_path}. You must only use absolute path, e.g. "/root/.local/bin/service_name arg1 arg2 arg3..."')
            exit(1)

    def prepare(
            self,
            service_name: str,
            script_path: str,
            description: str,
            start_after: str ='network.target',
            restart_always: bool =False,
            check_path: bool =False):
        '''
        Prepare service content for install.
        Args:
            service_name: The main service name, e.g. keystore
            script_path:  You must only use absolute path, e.g. "/root/.local/bin/service_name"
            description: e.g. My service description
            start_after: e.g. network.target
            restart_always: True or False
        Returns:
            str: Prepared multistring content
        '''
        if check_path: self._validate_path(script_path)
        restart_line = "Restart=always" if restart_always else ""

        service_content = f"""[Unit]
Description={description}
After={start_after}

[Service]
ExecStart={script_path}
Type=simple
{restart_line}

[Install]
WantedBy=multi-user.target
Alias={service_name}.service
"""
        return service_content

    def install(self, service_name: str, service_content: str):
        '''
        Install systemd service.
        Args:
            service_name: The main service name, e.g. keystore
            service_content: The main service content, e.g. 
            "
                [Unit]
                Description=My service description
                After=network.target auditd.service

                [Service]
                ExecStart=/root/.local/bin/service.sh
                Type=simple
                Restart=always

                [Install]
                WantedBy=multi-user.target
                Alias=service_name.service
            "
        You can prepare service by "prepare" function
        Returns True if all right
        '''
        service_name = f'{service_name}.service'
        service_path = f"/etc/systemd/system/{service_name}"

        if os.path.exists(service_path):
            self.__logger.error(f'{service_path} already exist')
            return
        with open(service_path, 'w') as f:
            self.__logger.log(f'Write {service_name} to {service_path}...')
            f.write(service_content)

        self.__logger.log('Reload systemd daemon...')
        reload_cmd = "systemctl daemon-reload"
        self.__runner.run(reload_cmd, exit_on_err=True)
        enable_cmd = f"systemctl enable {service_name}"
        self.__logger.log(f'Enable {service_name} daemon...')
        self.__runner.run(enable_cmd, exit_on_err=False)
        return True
    
    def start(self, service_name:str):
        start_cmd = f"systemctl start {service_name}"
        self.__logger.log(f'Start {service_name} daemon...')
        self.__runner.run(start_cmd, exit_on_err=True)
        return True

    def remove(self, service_name:str):
        '''
        Prepare service content for install.
        Args:
            service_name: The main service name, e.g. keystore
        Returns True if all right
        '''
        service_name = f'{service_name}.service'
        service_path = f"/etc/systemd/system/{service_name}"
        if not os.path.exists(service_path):
            self.__logger.error(f'{service_path} not exist')
            return

        self.__logger.log(f'Stop {service_name} daemon...')
        stop_cmd = f'systemctl stop {service_name}'
        self.__runner.run(stop_cmd, exit_on_err=True)
        self.__logger.log(f'Disable {service_name} daemon...')
        disable_cmd = f'systemctl disable {service_name}'
        self.__runner.run(disable_cmd, exit_on_err=True)
        if os.path.exists(service_path):
            os.remove(service_path)
        self.__logger.log('Reload systemd daemon...')
        reload_cmd = "systemctl daemon-reload"
        self.__runner.run(reload_cmd, exit_on_err=True)
        return True