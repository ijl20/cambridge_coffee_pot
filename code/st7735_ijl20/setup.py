from setuptools import setup

setup(
    name='ST7735',
    version='0.1',
    description='ST7735 Python Library for Raspberry Pi',
    py_modules=['ST7735'],
    install_requires=['Rpi.GPIO', 'spidev', 'numpy'],
)

