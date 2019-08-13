
pug
==
**Pug, the UDK Guide dog** that recudes the code maintenance complexity and simplifies the build process of UDK.

This is a Python/Pypi package.


## To create and test the Pypi package locally
1. ...
2. `edit tox.ini`
3. `update setup.py, setup.cfg, __init__.py`
4. `tox .`
5. `python setup.py sdist bdist_wheel`
6. `pip install --user dist/ipug-THE-LATEST-VERSION.tar.gz`

# Upload to Pypi
1. `twine upload dist/ipug-THE-LATEST-VERSION.{tar.gz, whl}`
2. or, `twine upload dist/*`

## Ref.
- http://otuk.kodeten.com/making-a-python-package-for-pypi---easy-steps/

