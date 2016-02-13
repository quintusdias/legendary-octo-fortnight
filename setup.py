from setuptools import setup

setup(
    name='XmpInPdf',
    author='John Evans',
    version='0.0.1',
    packages=['xmpinpdf'],
    entry_points={
        'console_scripts': ['spdfinfo=xmpinpdf.commandline:pdfinfo']
    }
)

