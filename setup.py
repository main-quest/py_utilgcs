from setuptools import setup, find_packages

# How to structure a python main package: https://stackoverflow.com/a/54613085
install_requires = open("requirements.txt", "r").read().splitlines()

# Converts git urls like '<protocol>://<repo>.git@<ref>#egg=<egg_name>'
# to '<egg_name> @ <protocol>://<repo>.git@<ref>' so it can be compatible with install_requires
for i in range(len(install_requires)):
    line = install_requires[i]
    if 'http' not in line:
        continue

    url_parts = line.split('#egg=')
    first_url_part = url_parts[0]
    egg = url_parts[1]
    install_requires[i] = f'{egg} @ {first_url_part}'

# Remove any comments
install_requires = [line for line in install_requires if not line.startswith('#')]
pkg_name = 'py_utilgcs'

setup(
    name='py_utilgcs',
    version='0.0.1',
    description="Partial wrapper around Google Cloud Storage. " +
                "'Install by 'pip install --upgrade git+https://github.com/main-quest/py_utilgcs.git#egg=py_utilgcs'",
    url='https://github.com/main-quest/py_utilgcs.git',
    author='The Fallen Games',
    author_email='contact@thefallengames.com',
    license='unlicense',
    # packages=['py_utilgcs'],
    packages=find_packages(exclude=["tests", "*.tests", "*.tests.*", "tests.*"]),
    zip_safe=False,

    # This field lists other packages that your project depends on to run.
    # Any package you put here will be installed by pip when your project is
    # installed, so they must be valid existing projects.
    #
    # For an analysis of "install_requires" vs pip's requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=install_requires
)
