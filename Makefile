# help:
#     @echo "    init"
#     @echo "        Install dependencies."
#     @echo "    clean-pyc"
#     @echo "        Remove python artifacts."
#     @echo "    test"
#     @echo "        Run py.test"
.PHONY: clean-pyc abi deploy

init:
	pip install -r requirements.txt

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

test: clean-pyc
	python -m unittest discover tests.python

abi:
	python deploy/ethabi.py

deploy:
	python deploy/ethdeploy.py --f deploy/tokenSale.json