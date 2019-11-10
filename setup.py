# Guides:
# https://packaging.python.org/tutorials/packaging-projects/
# https://packaging.python.org/guides/distributing-packages-using-setuptools/
# References:
# https://github.com/jendrikseipp/txt2tags/blob/master/setup.py
# https://github.com/mystor/git-revise/blob/master/setup.py
# https://github.com/docopt/docopt/blob/master/setup.py
# https://github.com/psf/requests/blob/master/setup.py
# https://github.com/psf/black/blob/master/setup.py
# https://github.com/pypa/pip/blob/master/setup.py

import setuptools

import sedparse

with open("README.md", "r") as fh:
    LONG_DESCRIPTION = fh.read()

setuptools.setup(
    name="sedparse",
    version=sedparse.__version__,
    author="Aurelio Jargas",
    author_email="aurelio@aurelio.net",
    description="GNU sed's parser translated from C to Python",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    url="https://github.com/aureliojargas/sedparse",
    project_urls={
        "Bug Tracker": "https://github.com/aureliojargas/sedparse/issues",
        "Source Code": "https://github.com/aureliojargas/sedparse",
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python",
        "Topic :: Software Development",
    ],
    py_modules=["sedparse"],
    python_requires=">=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*",
    entry_points={"console_scripts": ["sedparse = sedparse:entrypoint"]},
)
