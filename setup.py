from setuptools import find_packages, setup

__AUTHOR__ = "Federico Lolli"
__version__ = "v0.1a1"


setup(
    name="forecaster",
    version=__version__,
    packages=find_packages(),
    install_requires=[
        'scipy',
        'pyyaml',
        'trading212api',
        'python-telegram-bot',
        'raven',
        'termcolor',
    ],
    test_requirements=[
        'pytest',
        'pytest-pep8',
        'pytest-cov',
        'flake8',
    ],
    include_package_data=True,
    package_data={'': ['logs/.gitkeep', '**/*.yml', 'run.sh']},
    zip_safe=False,
    author="Federico Lolli",
    author_email="federico123579@gmail.com",
    description="Package that predict using algorithms",
    license="MIT",
    keywords="trading forecast algorithm",
    url="https://github.com/federico123579/forecaster",
    entry_points={
        'console_scripts': [
            'forecaster = forecaster.__main__:main'
        ]
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: User Interfaces',
        'Topic :: System :: Emulators'
    ]
)
