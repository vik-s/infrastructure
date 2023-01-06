install:
	@./prereqs.sh
	@echo "Ansible Vault pre-hook script setup and vault password set"

gitupdate:
	@./gitupdate.sh
	@echo "Completed github check in"

gaara:
	ansible-playbook -u ansible -b run.yaml --limit gaara --vault-password-file .vault-pass

tsukuyomi:
	ansible-playbook -u ansible -b run.yaml --limit tsukuyomi --vault-password-file .vault-pass

dockermain:
	ansible-playbook -u ansible -b run.yaml --limit dockermain --vault-password-file .vault-pass

sakura:
	ansible-playbook -u ansible -b run.yaml --limit sakura --vault-password-file .vault-pass

tartarus:
	ansible-playbook -u ansible -b nub.yaml --limit tartarus --vault-password-file .vault-pass

docker-update:
	ansible-playbook -u ansible -b docker-update.yaml --vault-password-file .vault-pass
