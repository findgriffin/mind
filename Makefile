
build: style types test

venv:
	python3 -m venv venv

venv/pip.log: requirements.txt
	pip3 install -r requirements.txt

install: venv venv/pip.log
	echo "#! /bin/sh" > activate
	echo ". ./venv/bin/activate" >> activate
	chmod +x activate
	./activate; \

activate:
	set -a && . ./venv/bin/activate && set +a
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

clean:
	rm -rf venv
	rm -rf **/__pycache__
	rm -rf **/*.pyc
