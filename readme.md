# Decription
Script 'ssh-mounter' for automate creation and connection remote user folder to current system.
# Installation from test.pypi.org
```bash
pipx install -i https://test.pypi.org/simple/ ssh-mounter
```
[//]: # (todo add to main pypi.org repo)
# Base usage:
```bash
ssh-mounter -u username -c StrongUserPassword -s remote-server.com -r /home/username -m /mnt/local_path -l
```
It's create remote user at remote server. Create SSH certificate file in interactive mode and mount remote user home directory.
More usage information you can see by `ssh-mounter -h`

[//]: # (build command: rm dist -r -Force ; py -m build ; py -m twine upload --repository testpypi dist/*)