from setuptools import setup, find_packages


setup(
    name="fogbed",
    version="1.0.0",
    packages=find_packages(),
    description='Containernet fork that add Fogbed support.',
    long_description='Containernet fork that add Fogbed support.',
    keywords=['networking', 'emulator', 'protocol', 'Internet', 'OpenFlow', 'SDN', 'fog'],
    include_package_data=True,
    url='https://github.com/EsauM10/fogbed',
    author='Esaú Mascarenhas',
    author_email='esaumasc@gmail.com',
    classifiers=[
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Topic :: System :: Emulators'
    ]
)