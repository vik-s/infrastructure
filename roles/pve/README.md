## Adding new LXC containers
- Open `vars/vault.yaml` for edit using `ansible-vault edit --vault-password .vault-pass vars/vault.yaml`.
- Define a new LXC container (default template: Alpine) in the `lxc_mnts` variable.
- Ensure `setup_infra = true`.
- Run `make gaara`.

## Adding new disks to SnapRaid Array
- Drive formatting and partitioning is done manually using `gpart`.
- Define the disk in `roles/pve/vars/main.yaml` under the `data_disks` or `parity_disks` variable.
- Ensure `setup_disks = true`.
- Run `make gaara`.

## Enabling Wireguard (if running an application like wg-easy)
- Right now, I am running Wireguard in pfSense. I'll document this if I switch to running a container. The role works though.

## Docker services on PVE host
- Only applications which _need_ to be on the host machine. Other applications are run in the `dockermain` LXC.
- Define services in `roles/pve/files/docker-compose.yaml`.
