.PHONY: help docs-check docs-publish

help:
	@echo "Commandes disponibles :"
	@echo "  make docs-check    - importe, construit et valide la documentation Forge sans publier"
	@echo "  make docs-publish  - publie la documentation Forge sur forgemvc.com"

docs-check:
	bash scripts/sync-forge-docs-and-deploy.sh

docs-publish:
	DRY_RUN=0 bash scripts/sync-forge-docs-and-deploy.sh
