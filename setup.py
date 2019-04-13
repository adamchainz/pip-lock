import re

from setuptools import setup


def get_version(filename):
    with open(filename, 'r') as fp:
        contents = fp.read()
    return re.search(r"__version__ = ['\"]([^'\"]+)['\"]", contents).group(1)


version = get_version('pip_lock.py')


with open('README.rst', 'r') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst', 'r') as history_file:
    history = history_file.read()


setup(
    name='pip-lock',
    version=version,
    description="Check for differences between requirements.txt files and your environment.",
    long_description=readme + '\n\n' + history,
    author="Aaron Kirkbride, Adam Johnson, et al.",
    author_email='me@adamj.eu',
    url='https://github.com/adamchainz/pip-lock',
    py_modules=['pip_lock'],
    include_package_data=True,
    python_requires='>=3.4',
    license="ISCL",
    zip_safe=False,
    keywords='pip, requirements',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: ISC License (ISCL)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python',
        'Topic :: Utilities',
    ],
)
