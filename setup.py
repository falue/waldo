from setuptools import setup, find_packages

setup(
    name='waldo',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Adafruit_MotorHAT',
        'Click',
        'evdev',
        'pyserial',
        'pyyaml',
        'RPi.GPIO',
        'serial',
    ],
    entry_points='''
        [console_scripts]
        waldo=waldo.scripts.cli:cli
        waldo_old=waldo.scripts.cli_old:cli
    ''',
    use_scm_version=True,
    setup_requires=['pytest-runner', 'setuptools_scm'],
    tests_require=['pytest'],
)
