# infrastructure
Ansible Homelab Infrastructure

`make bootstrap` - Set up user name, ansible user, transfer SSH keys over, and harden SSH config. If this fails, make sure you comment out the `remote_user = ansible` line and `become_ask_pass=False` lines in the ansible.cfg file. These users do not exist in the first bootstrap run, but will do so after the users and keys have been setup properly.
