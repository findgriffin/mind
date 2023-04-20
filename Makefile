
build: style types test

venv:
	python3 -m venv venv

venv/pip.log: requirements.txt
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
	mypy mind

test:
	coverage run --source mind -m unittest discover -s tests/unit
	coverage html
	coverage report --fail-under=90

perf:
	python -m unittest discover -s tests/perf

deploy:	build git-clean
	git push
	
git-clean:
	git diff-index --quiet HEAD
	test -z "$(git status --porcelain)"

branch:
	git branch --show-current

run:
	./run.py

local:
	./mind/app.py

clean:
	rm -rf venv
	rm -rf **/__pycache__
	rm -rf **/*.pyc
