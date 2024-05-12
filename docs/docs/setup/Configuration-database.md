# Configuration - Database Settings

The CSE supports different types of databases. The database settings are configured in the configuration file under the section `[database]` and its subsections.


##	General Settings

**Section: `[database]`**

These are the general database settings.

| Setting        | Description                                                                                                                                        | Default                                                                                                                     | Configuration Name      |
|:---------------|:---------------------------------------------------------------------------------------------------------------------------------------------------|:----------------------------------------------------------------------------------------------------------------------------|:------------------------|
| backupPath     | The directory for a backup of the database files.<br />Database backups are not supported for the in-memory database and postgreSQL.               | [${basic.config:baseDirectory}](../setup/Configuration-introduction.md#built-in-settings)/data/backup | database.backupPath     |
| resetOnStartup | Reset the databases at startup.<br/>See also command line argument [--db-reset](../setup/Running.md).                                              | False                                                                                                                       | database.resetOnStartup |
| type           | The type of database to use.<br />See also command line argument [--db-type](../setup/Running.md).<br />Allowed values: tinydb, postgresql, memory | tinydb                                                                                                                      | database.type           |


## TinyDB

**Section: `[database.tinydb]`**

These are the settings for the TinyDB database. The *cacheSize* and *writeDelay* settings are only used if the database type is set to *tinydb* (ie. in file-based mode). They have a major impact on the performance of the database.

| Setting    | Description                                                                                  | Default                                                                                                              | Configuration Name         |
|:-----------|:---------------------------------------------------------------------------------------------|:---------------------------------------------------------------------------------------------------------------------|:---------------------------|
| cacheSize  | Cache size in bytes, or 0 to disable caching.                                                | 0                                                                                                                    | database.tinydb.cacheSize  |
| path       | Directory for the database files.                                                            | [${basic.config:baseDirectory}](../setup/Configuration-introduction.md#built-in-settings)/data | database.tinydb.path       |
| writeDelay | Delay in seconds before new data is written to disk to avoid trashing. Must be full seconds. | 1 second                                                                                                             | database.tinydb.writeDelay |


## PostgreSQL

**Section: `[database.postgresql]`**

These are the settings for the PostgreSQL database. 

| Setting  | Description                              | Default                                                                                 | Configuration Name           |
|:---------|:-----------------------------------------|:----------------------------------------------------------------------------------------|:-----------------------------|
| database | Name of the database.                    | [${basic.config:cseID}](../setup/Configuration-basic.md#basic-configuration) | database.postgresql.database |
| host     | Hostname of the PostgreSQL server.       | localhost                                                                               | database.postgresql.host     |
| password | Password for the database.               | not set                                                                                 | database.postgresql.password |
| port     | Port of the PostgreSQL server.           | 5432                                                                                    | database.postgresql.port     |
| schema   | Name of the schema.<br/>Default: acmecse | acmecse                                                                                 | database.postgresql.schema   |
| role     | Login/Username for the database.         | [${basic.config:cseID}](../setup/Configuration-basic.md#basic-configuration) | database.postgresql.role     |
