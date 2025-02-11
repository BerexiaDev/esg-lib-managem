# ESG Global Library
1. audit_logger_module
2. decorators
3. Paginator
4. reqparse
5. Document

## Push to pypi
```bash
pip install wheel
python setup.py sdist bdist_wheel
pip install twine
twine upload dist/*
```
