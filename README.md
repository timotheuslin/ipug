
pug
==
**Pug, the Udk Guidedog** that reduces the code maintenance complexity and simplifies the build process of UDK.

This is a Python/Pypi package.


## To create and test the Pypi package locally
1. ...
2. `edit tox.ini`
3. `update the (version) content of setup.py, setup.cfg, __init__.py`
4. `run tox .`
5. `pip install . --user --upgrade` and test ipug on a unit-test project.
5. `python setup.py sdist bdist_wheel`
6. `pip install --user dist/ipug-THE-LATEST-VERSION.tar.gz` e.g. `pip install --user dist/ipug-0.2.0.tar.gz`

## Upload to Pypi
1. `twine upload dist/ipug-THE-LATEST-VERSION.{tar.gz, whl}` e.g. `twine upload dist/ipug-0.2.0.tar.gz`
2. or, `twine upload dist/*`

## Ref.
- http://otuk.kodeten.com/making-a-python-package-for-pypi---easy-steps/
- [Todo-list](https://hackmd.io/SeYaoagMTkeJEF6LrM6DPw?view)
