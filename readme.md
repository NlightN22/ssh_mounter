# Decription
Script 'ssh-mounter' for automate creation and connection remote user folder to current system.
# Installation from test.pypi.org
```bash
pipx install -i https://test.pypi.org/simple/ ssh-mounter
# or
pip3 install -i https://test.pypi.org/simple/ ssh-mounter
```
[//]: # (todo add to main pypi.org repo)

# Examples of usage:
## Base usage for new user and new SSH certificate:
```bash
ssh-mounter -u username -c StrongUserPassword -s remote-server.com -r /home/username -m /mnt/local_path -l
```
It's create remote user at remote server. Create SSH certificate file in interactive mode and mount remote user home directory.
## Already created user without created certificate:
```bash
ssh-mounter -u username -s remote-server.com -r /home/username -m /mnt/local_path -l
```
## Already created user and default certificate:
```bash
ssh-mounter -u username -s remote-server.com -r /home/username -m /mnt/local_path -l
```
## Already created user and certificate:
```bash
ssh-mounter -u username -s remote-server.com -r /home/username -m /mnt/local_path -k ~/.ssh/certificate -l
```
## Full interactive mode:
```bash
ssh-mounter
```
## If you want to install service wich automatically run this script:
```bash
ssh-mounter -u username -s remote-server.com -r /home/username -m /mnt/local_path -l -i
```
## If you want to remove service wich automatically run this script:
```bash
ssh-mounter -u username -s remote-server.com -r /home/username -m /mnt/local_path -l -d
```
More information you can see by command `ssh-mounter -h`

[//]: # (build command: rm dist -r -Force ; py -m build ; py -m twine upload --repository testpypi dist/*)
[//]: # (pipx upgrade -i https://test.pypi.org/simple/ ssh-mounter)
[//]: # (pip3 install --upgrade -i https://test.pypi.org/simple/ ssh-mounter)

