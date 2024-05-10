# Integrating Into Other Projects

This article describes how to integrate the CSE into other applications and how to run it in a Jupyter Notebook.

## Introduction

It is possible to integrate the CSE into other applications. In this case you would possibly like to provide startup arguments, for example the path of the configuration file or the logging level, directly instead of getting them from the command line via *argparse*.

You might want to get the example from the main file [acme/\_\_main__.py](https://github.com/ankraft/ACME-oneM2M-CSE/tree/master/acme/__main__.py) where you could replace the line:

```python title="Replace this line from the main file"
CSE.startup(parseArgs())
```

with a call to the CSE's *startup()* function for your application:

```python title="Call the CSE's startup function"
CSE.startup(None, configfile=defaultConfigFile, loglevel='error')
```

!!! note
	The first argument of the *startup()* function is the *argparse* arguments. In case you provide the arguments directly the first argument may need to be `None`. 

The names of the *argparse* variables can be used here, and you may provide all or only some of the arguments. Please note that you need to keep or copy the `import` and `sys.path` statements at the top of that file.


### Jupyter Notebooks

Since ACME CSE is written in pure Python it can be run in a Jupyter Notebook. The following code could be copied to a notebook cell to run the CSE.

```python title="Run the CSE in a Jupyter Notebook"
# Increase the width of the notebook to accommodate the log output
from IPython.display import display, HTML
display(HTML("<style>.container { width:100% !important; }</style>"))

# Change to the CSE's directory and start the CSE
# Ignore the error from the %cd command
%cd -q tools/ACME   # adopt this to the location of the ACME CSE
%run -m acme -- --headless
```

Note the following:

- The CSE should be run in *headless* mode to avoid too much output to the notebook.
- Once executed the notebook cell will not finish its execution. It is therefore recommended to run the CSE in a separate notebook.
- The CSE can only be stopped by stopping or restarting the notebook's Python kernel.
