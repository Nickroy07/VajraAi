.PHONY: setup backend-test dashboard-build mobile-typecheck

setup:
	bash scripts/setup.sh

backend-test:
	cd backend && pytest -q

dashboard-build:
	cd dashboard && npm run build

mobile-typecheck:
	cd mobile && npm run typecheck
