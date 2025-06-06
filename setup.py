from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in excel_hr/__init__.py
from excel_hr import __version__ as version

setup(
	name="excel_hr",
	version=version,
	description="Excel Technologies HR Solutions ",
	author="Shaid Azmin",
	author_email="azmin@excelbd.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
