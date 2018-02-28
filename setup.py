from setuptools import find_packages, setup

from forecaster import __VERSION__

setup(
    name="forecaster",
    version=__VERSION__,
    packages=find_packages(),
    install_requires=[
        'pandas',
        'numpy',
        'scikit-learn',
        'pyyaml',
        'trading212-api',
        'python-telegram-bot',
    ],
    include_package_data=True,
    package_data={'': ['logs/.gitkeep', '**/*.yml']},
    zip_safe=False,
    author="Federico Lolli",
    author_email="federico123579@gmail.com",
    description="Package that predict using algorithms",
    license="MIT",
    keywords="trading forecast algorithm",
    url="https://github.com/federico123579/forecaster",
    entry_points={
        'console_scripts': [
            'forecaster = forecaster.bot:main'
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
