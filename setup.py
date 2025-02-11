from setuptools import setup, find_packages

setup(
    name='esg_lib',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        "cryptography==42.0.8",
        "flask-restx==1.1.0",
        "inject==5.0.0",
        "cryptography==42.0.8",
        "python-dotenv==0.21.1",
        "PyJWT==2.8.0",
    ],
    description='ESG Global Library',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
