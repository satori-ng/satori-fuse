from setuptools import setup




__version__ = '0.1.1'
__name__ = 'satori-fuse'
__desc__ = 'The System Image Mount Tool of the Satori-Suite'
__email__ = 'satori_ng@email.com'
__url__ = 'https://github.com/satori-ng/'


with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name=__name__,
    description=__desc__,
    version=__version__,
    url=__url__,

    author="Satori-NG org",
    author_email=__email__,

    py_modules=['mount'],
    entry_points={
        "console_scripts": [
            "satori-mount=mount:main",
        ],
    },
    install_requires=requirements,

)


