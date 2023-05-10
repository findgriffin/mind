FUNCTION=mind-prod
REGION = us-west-2
ENVCHAIN = findgriffin
APP=mind
ENV=prod
PYTHON=python3.10

clean:
	rm -rf build

build: clean install style types test
	mkdir -p build/site-packages
	zip -r build/$(APP)-$(ENV).zip $(APP) -x "*__pycache__*"
	pip install -r $(APP)/requirements.txt -t build/site-packages
	cd build/site-packages; zip -g -r ../$(APP)-$(ENV).zip . -x "*__pycache__*"

deploy: build
	envchain $(ENVCHAIN) aws lambda update-function-code \
		--region=$(REGION) \
		--function-name $(FUNCTION) \
		--zip-file fileb://build/$(FUNCTION).zip \
		--publish


venv:
	python3 -m venv venv

venv/pip.log: requirements.txt venv
	pip3 install -r requirements.txt > venv/pip.log

activate.sh:
	echo "#! /bin/sh" > activate.sh
	echo ". ./venv/bin/activate" >> activate.sh
	chmod +x activate.sh
	
install: venv venv/pip.log activate.sh

activate:
	set -a && ./activate.sh && set +a
style:
	flake8 mind tests

types:
	mypy mind --ignore-missing-imports

test: install
	coverage run --source mind -m unittest discover -s tests/unit
	coverage html
	coverage report --fail-under=90

perf:
	python -m unittest discover -s tests/perf

push: build git-clean
	git push
	
git-clean:
	git diff-index --quiet HEAD
	test -z "$(git status --porcelain)"

branch:
	git branch --show-current

run:
	./run.py

local:
	FLASK_ENV=development ./mind/app.py

full-clean:	clean
	rm -rf venv
	rm -rf **/__pycache__
	rm -rf **/*.pyc
