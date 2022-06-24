import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name='libpcocheckin',
    version='0.5',
    author='David Hudson',
    author_email='unpublished',
    description='Functions for working with Planning Center Online Check-in API',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/jcc-dhudson/libpcocheckin',
    project_urls = {
        "Bug Tracker": "https://github.com/jcc-dhudson/libpcocheckin/issues"
    },
    license='MIT',
    packages=['libpcocheckin'],
    install_requires=['pypco'],
)