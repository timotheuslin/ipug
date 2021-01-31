How to build and upload iPug to PypI
==

## To create and test the Pypi package locally
1. ...
2. edit `tox.ini`
3. update the (version) content of `setup.py, setup.cfg, __init__.py`
4. run `tox .`
5. `python -m pip install . --user --upgrade` and test ipug on a unit-test project.
6. `python setup.py sdist bdist_wheel`
7. `python -m pip install --user dist/ipug-THE-LATEST-VERSION.tar.gz` e.g. `pip install --user dist/ipug-0.2.3.tar.gz`

## Upload to PyPI
1. `twine upload dist/ipug-THE-LATEST-VERSION.{tar.gz, whl}` e.g. `twine upload dist/ipug-0.2.3.tar.gz`
2. or, `twine upload dist/*`

## Ref.
- http://otuk.kodeten.com/making-a-python-package-for-pypi---easy-steps/
- [Todo-list](https://hackmd.io/SeYaoagMTkeJEF6LrM6DPw?view)
- Pip-install using github: `python -m pip install --user --upgrade git+https://github.com/timotheuslin/ipug`
