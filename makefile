enstall:
	@./prereqs.sh
	@echo "Ansible Vault pre-hook script setup and vault password set"

encrypt:
	ansible-vault encrypt --vault-password-file .vault-pass vars/vault.yaml

decrypt:
	ansible-vault decrypt --vault-password-file .vault-pass vars/vault.yaml

gitupdate:
	@./gitupdate.sh
	@echo "Completed github check in"

gaara:
	ansible-playbook -u ansible -b run.yaml --limit gaara --vault-password-file .vault-pass

kakashi:
	ansible-playbook -u ansible -b run.yaml --limit kakashi --vault-password-file .vault-pass

dockermain:
	ansible-playbook -u ansible -b run.yaml --limit dockermain --vault-password-file .vault-pass
