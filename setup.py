from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = f.read().strip().split("\n")

setup(
    name="appz_hosting",
    version="0.0.1",
    description="AppZ Studio - White-label Managed Hosting Platform",
    author="Simbotix",
    author_email="rajesh@simbotix.com",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires,
)
