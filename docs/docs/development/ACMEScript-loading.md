# Loading & Running ACMEScripts

By default scripts are stored in and are imported from the *init* directory and in its sub-directories, which names end with *.scripts*. They are imported from the [secondary *init* directory](../setup/Running.md#secondary-init-directory) as well. In addition, one can specify a [list of directories](../setup/Configuration-scripting.md) in the configuration file with additional scripts that will be imported from those directories.

All files in those directories with the extension `.as` are treated as ACMEScript files and are automatically imported during CSE startup, and are also imported and updated during runtime if a file changes.

## Running Scripts

There are many different ways to run scripts:

- Scripts can be manually run from the console interface with the `R` (Run) command.
- They can also be run by a specified keypress from the console interface (see the [onKey](ACMEScript-metatags.md#onkey) meta tag).
- Scripts can be scheduled to run at specific times or dates. This is similar to the Unix cron system (see the [at](ACMEScript-metatags.md#at) meta tag).
- It is possible to schedule scripts to run at certain events. Currently, the CSE [init](ACMEScript-metatags.md#init), [onStartup](ACMEScript-metatags.md#onstartup), [onRestart](ACMEScript-metatags.md#onrestart), and [onShutdown](ACMEScript-metatags.md#onshutdown) events are supported.
- Scrips can be run as a receiver of a NOTIFY request from the CSE. See the [onNotification](ACMEScript-metatags.md#onnotification) meta tag.
- They can also be run as a command of the [Upper Tester Interface](../setup/Operation-uppertester.md).
- Scripts can be integrated as tools in the [Text UI](../setup/TextUI.md). See also the section [Text UI meta-tags](../development/ACMEScript-metatags.md#text-ui) for available tags.


## Script Arguments

Scripts may have arguments that can be accessed with the [argv](ACMEScript-functions.md#argv) function and [argc](ACMEScript-variables.md#argc) variable.

!!! Note
	Not all of the above methods support script arguments. For example, scripts that are run by the [onStartup](ACMEScript-metatags.md#onstartup), [onRestart](ACMEScript-metatags.md#onrestart), or [onShutdown](ACMEScript-metatags.md#onshutdown) events do not support arguments.


## Script Prompt

A script may ask for input before it runs. This can be enabled with the [@prompt](ACMEScript-metatags.md#prompt) meta tag. The prompt's answer is then assigned as the script's first argument.

!!! Warning "Attention"
	The [@prompt](ACMEScript-metatags.md#prompt) meta tag should only be used when human interaction can be ensured. Running a script with this meta tag, for example, [scheduled](ACMEScript-metatags.md#at) or unattended will cause the script to wait forever for user input. 


## Running Scripts at Startup, Restart, and Shutdown

Right after a CSE finished the start-up or restart, or just before a CSE shuts down it looks for scripts that have the [@onStartup](ACMEScript-metatags.md#onstartup), [@onRestart](ACMEScript-metatags.md#onrestart), or [@onShutdown](ACMEScript-metatags.md#onshutdown) meta tags set, and runs them respectively.

## Initialization Script

Whenever a CSE starts or is restarted (or reset) it is necessary to create couple of oneM2M resources and to build a basic resource tree. This is done by running a script that has the [@init](ACMEScript-metatags.md#init) meta tag set. A script with this tag is executed right after the start of the internal services during the initialization of the *importer* service.

!!! Info "Note"
	Only one script must have the [@init](ACMEScript-metatags.md#init) meta tag set. By default this is the [init.as](https://github.com/ankraft/ACME-oneM2M-CSE/blob/master/acme/init/init.as){target=_new} script from the CSE's [init](https://github.com/ankraft/ACME-oneM2M-CSE/blob/master/acme/init){target=_new} directory.



