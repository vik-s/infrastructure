#!/bin/bash

ansible-galaxy role install -r requirements.yaml
echo "Ansible Galaxy roles installed"
ansible-galaxy collection install -r requirements.yaml
echo "Ansible Galaxy collections installed"
./git-init.sh
echo "Ansible vault git pre-commit hook installed"

read -p "Add Ansible Vault Password: " pass
if [ -d / ]; then
rm .vault-pass
cat <<EOT >> .vault-pass
$pass
EOT

fi

chmod 0600 .vault-pass
