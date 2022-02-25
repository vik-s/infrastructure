# infrastructure
Ansible Homelab Infrastructure

- Run `make install` to install the necessary galaxy roles as specified in `requirements.yaml`. This will also install the git-precommit hook and setup vault password if it does not exist.

- Run `make gaara`. This will setup the Proxmox host, spin up containers, wireguard (if needed), disk arrays and snapraid. Finally docker apps on host are installed. To control the execution of certain roles, the corresponding flags `setup_containers`, `setup_wireguard`, `setup_snapraid`, and `setup_disks` must be set accordingly.

- Run `make dockermain`. This will setup the Docker LXC and install the docker-compose file. Start all services by running `docker-compose --profile all up -d`.
