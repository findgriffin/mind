FUNCTION=mind-prod
REGION = us-west-2
ENVCHAIN = findgriffin
APP=mind
ENV=prod
PYTHON=python3.10
LIBRARIES=lib
FUNCTION_URL="https://2lzl5j3eoqpgqzl2avqcqtkygi0uwfkh.lambda-url.us-west-2.on.aws/"

clean:
	rm -rf build

build/$(APP)-$(ENV).zip: clean install style types test mind
	mkdir -p build/site-packages
	zip -r build/$(APP)-$(ENV).zip $(APP) -x "*__pycache__*"
	zip -r build/$(APP)-$(ENV).zip $(LIBRARIES) -x "*__pycache__*"
	pip install -r $(APP)/requirements.txt -t build/site-packages
	cd build/site-packages; zip -g -r ../$(APP)-$(ENV).zip . -x "*__pycache__*"

build: build/$(APP)-$(ENV).zip

deploy: build/$(APP)-$(ENV).zip
	envchain $(ENVCHAIN) aws lambda update-function-code \
		--region=$(REGION) \
		--function-name $(FUNCTION) \
		--zip-file fileb://build/$(FUNCTION).zip \
		--publish


venv:
	python3 -m venv venv

venv/pip.log: requirements.txt mind/requirements.txt venv
	pip3 install -r requirements.txt > venv/pip.log

activate.sh:
	echo "#! /bin/sh" > activate.sh
	echo ". ./venv/bin/activate" >> activate.sh
	chmod +x activate.sh
	
install: venv venv/pip.log

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

check_prod:
	envchain findgriffin aws --region=us-west-2 lambda get-function --function-name mind-prod | jq '.Configuation.State'

test_prod:
	curl -v -X POST "$FUNCTION_URL" -H 'X-Forwarded-Proto: https' -H 'content-type: application/json' -d '{ "example": "test" }'
