# Installing ACME on a Raspberry Pi

Doing installations on a Raspberry Pi, especially on older versions, could be a small challenge, because some of the external Python packages require extra libraries that are not necessarily available on an old Raspberry Pi.

This guide presents the necessary steps to install Python 3.11, the external Python packages and ACME on an older Raspberry Pi 3B with Raspberry Pi OS (32 bit).

## Installing Python and Tools

First, we need to install a newer Python 3 runtime on our Raspberry Pi.

### Downloading Python Source

The following download gets the source code from the official Python repository. It could be a newer version of Python as well, of course.

```sh
wget https://www.python.org/ftp/python/3.11.4/Python-3.11.4.tgz
```

### Installing Extra Components

The following commands install the necessary system libraries and other tools to compile Python on the Raspberry Pi. :

```sh
sudo apt update
sudo apt-get install -y build-essential tk-dev libncurses5-dev libncursesw5-dev libreadline6-dev libdb5.3-dev libgdbm-dev libsqlite3-dev libssl-dev libbz2-dev libexpat1-dev liblzma-dev zlib1g-dev libffi-dev libatlas-base-dev libgeos-dev gfortran git cmake libpq-dev
```

### Compile Python

The next step is to unpack and to unpack, configure, make and install the Python runtime.
 
```sh
tar -xzvf Python-3.11.4.tgz 
cd Python-3.11.4/
./configure --enable-optimizations
sudo make -j 4
sudo make altinstall
cd ..
```

## Downloading and Installing ACME

Next, we will install the ACME CSE. We have the choice to install it from the PyPi repository or to download the source code and install it manually.

=== "Installation with *pip* (Package Installation)"

	Run the following command to install ACME from the PyPi repository:

	```sh
	python -m pip install acmecse
	```

=== "Manual Installation"

	The following commands download the ACME repository.

	```sh
	git clone https://github.com/ankraft/ACME-oneM2M-CSE.git
	cd ACME-oneM2M-CSE
	```

	An alternative is to download the [latest](https://github.com/ankraft/ACME-oneM2M-CSE/releases/latest){target=_new} release as a zip package and unpack it.

<mark>TODO: Add running link</mark>


 