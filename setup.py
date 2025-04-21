from setuptools import setup, find_packages

setup(
    name='short_term_land_lord',
    version='0.1',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'flask',
    ],
) 