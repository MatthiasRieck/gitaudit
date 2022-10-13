import setuptools

setuptools.setup(
    name="gitaudit",
    version="0.0.1",
    author="Matthias Rieck",
    author_email="Matthias.Rieck@tum.de",
    description="Analyse git repositories",
    long_description="Analyse git repositories",
    url="https://github.com/MatthiasRieck/gitaudit",
    packages=setuptools.find_packages(exclude=["tests*"]),
    package_data={},
    include_package_data=True,
    install_requires=[],
)
