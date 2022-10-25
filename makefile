twine: build
	python3 -m twine upload dist/*   

build:
	-rm -vrf dist/
	python3 -m build

.PHONY: twine build
