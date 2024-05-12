# Installing ACME on a Raspberry Pi

Doing installations on a Raspberry Pi, especially on older versions, could be a small challenge, because some of the external Python packages require extra libraries that are not necessarily available on an old Raspberry Pi.

This guide presents the necessary steps to install Python 3.11, the external Python packages and ACME on an older Raspberry Pi 3B with Raspberry Pi OS (32 bit).

## Installing Python and Tools

First, we need to install a newer Python 3 runtime on our Raspberry Pi.

### Downloading Python Source

The following download gets the source code from the official Python repository. It could be a newer version of Python as well, of course.

```sh title="Download Python"
wget https://www.python.org/ftp/python/3.11.4/Python-3.11.4.tgz
```

### Installing Extra Components

The following commands install the necessary system libraries and other tools to compile Python on the Raspberry Pi. :

```sh title="Install Extra Components and Libraries"
sudo apt update
sudo apt-get install -y build-essential tk-dev libncurses5-dev libncursesw5-dev libreadline6-dev libdb5.3-dev libgdbm-dev libsqlite3-dev libssl-dev libbz2-dev libexpat1-dev liblzma-dev zlib1g-dev libffi-dev libatlas-base-dev libgeos-dev gfortran git cmake libpq-dev
```

### Compile Python

The next step is to unpack and to unpack, configure, make and install the Python runtime.

```sh title="Compile Python"
tar -xzvf Python-3.11.4.tgz 
cd Python-3.11.4/
./configure --enable-optimizations
sudo make -j 4
sudo make altinstall
cd ..
```

## Install, Configure, and Run ACME

Next, we will install the ACME CSE. 

You can now follow the instructions in the [Installation](../setup/Installation.md) guide to install the ACME CSE on your Raspberry Pi.



 