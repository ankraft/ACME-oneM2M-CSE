# How to Install pyenv

This guide shortly describes how to install the [pyenv](https://github.com/pyenv/pyenv){target=_new} virtual environment manager.
In addition, we will install [pyenv-virtualenv](https://github.com/pyenv/pyenv-virtualenv){target=_new}. This is a *pyenv* plugin for creating and managing virtual Python environments. 

Pyenv is only officially supported on Linux/MacOS systems, so we will focus on these OS environments.


## Prerequisites

### Homebrew

This guide assumes that you have installed the [homebrew](https://brew.sh){target=_new} package manager.

### MacOS: Xcode dependencies

If not done yet, we need to install the *Xcode* dependencies:

```sh title="Install Xcode dependencies"
Xcode-select --install
```


## Installing pyenv

Install *pyenv* using *homebrew*:

```sh title="Install pyenv"
brew upgrade
brew install pyenv
```

Install extra libraries:

```sh title="Install extra libraries"
brew install readline xz
```

Install *virtualenv* using *homebrew*:

```sh title="Install pyenv-virtualenv"
brew install pyenv-virtualenv
```


## Getting Started

We can now use *pyenv* and *pyenv-virtualenv*. We start with installing a Python version.

The following command installs *Python 3.11.7* in *pyenv*:

```sh title="Install a Python Version"
pyenv install 3.11.7
```

Since we want to keep the installed base Python version "clean2, we will create a new virtual environment, e.g. taking version *3.11.7* as a base version. The following command will create a virtual environment *acme-3.11* that can be used later on:

```sh title="Create a Virtual Environment"
pyenv virtualenv 3.11.7 acme-3.11
```


We can now enable a virtual environment for the local directory:

```sh title="Enable a virtual environment for the local directory"
pyenv local acme-3.11
```
