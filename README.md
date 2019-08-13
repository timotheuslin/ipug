
pug
==
**Pug, the UDK Guide dog** that recudes the code maintenance complexity and simplifies the build process of UDK.

This is a Python/Pypi package.


## To create and test the Pypi package locally
0. ...
1. `edit tox.ini`
2. `update setup.py, setup.cfg, __init__.py`
3. `tox .`
4. `python setup.py sdist bdist_wheel`
5. `pip install --user dist/ipug-THE-LATEST-VERSION.tar.gz`

# Upload to Pypi
0. twine upload dist/ipug-THE-LATEST-VERSION.tar.gz

## Ref.
- http://otuk.kodeten.com/making-a-python-package-for-pypi---easy-steps/

