.PHONY: dev build-frontend run

dev:
	python run.py

build-frontend:
	cd frontend && npm run build
	python -c "import shutil, pathlib; p=pathlib.Path('frontend_build'); shutil.rmtree(p, ignore_errors=True); shutil.copytree('frontend/out', p)"

run: dev
