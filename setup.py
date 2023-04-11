from setuptools import setup, find_packages


setup(
    name="fogbed",
    version="1.2.0",
    description='Containernet fork that add Fogbed support.',
    long_description='Containernet fork that add Fogbed support.',
    keywords=['networking', 'emulator', 'protocol', 'Internet', 'OpenFlow', 'SDN', 'fog'],
    url='https://github.com/EsauM10/fogbed',
    author='Esaú Mascarenhas',
    author_email='esaumasc@gmail.com',
    classifiers=[
        'Intended Audience :: Developers',
        'Programming Language :: Python 3.8',
        'Topic :: System :: Emulators'
        'Operating System :: Ubunbu OS'
    ],
    install_requires = [
        'clusternet @ https://github.com/EsauM10/clusternet/tarball/main#egg=clusternet'
    ],
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False
)