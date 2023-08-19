# Decription
Script 'ssh-mounter' for automate creation and connection remote user folder to current system.
# Installation from test.pypi.org
```bash
pipx install -i https://test.pypi.org/simple/ ssh-mounter
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
## Already created user and certificate:
```bash
ssh-mounter -u username -s remote-server.com -r /home/username -m /mnt/local_path -k ~/.ssh/id_rsa -l
```
## Full interactive mode:
```bash
ssh-mounter
```
More information you can see by command `ssh-mounter -h`

[//]: # (build command: rm dist -r -Force ; py -m build ; py -m twine upload --repository testpypi dist/*)