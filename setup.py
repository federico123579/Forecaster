from setuptools import setup, find_packages

setup(
    name="bitgen",
    version="v0.0.1",
    packages=find_packages(),
    install_requires=[
        'pyyaml',
        'python-telegram-bot'
    ],
    include_package_data=True,
    package_data={'': ['logs/.null.ini', '**/*.yml']},
    zip_safe=False,
    author="Federico Lolli",
    author_email="federico123579@gmail.com",
    description="Package to trade with cryptocurrencies with algorithms",
    license="MIT",
    keywords="trading bot crypto bitcoin",
    url="https://github.com/federico123579/bitgen",
    entry_points={
        'console_scripts': [
            'bitgen = bitgen.test:main'
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
