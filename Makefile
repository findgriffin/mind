
build: style types test

install:
	pip3 install -r requirements.txt

style:
	flake8 mind tests

types:
	mypy mind

test:
	coverage run --source mind -m unittest discover
	coverage html
	coverage report --fail-under=90

perf:
	python -m unittest tests.perf.test_fs_perf.TestFsPerf

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
	rm -rf **/__pycache__
	rm -rf **/*.pyc
