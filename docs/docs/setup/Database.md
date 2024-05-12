# Database Setup

The ACME CSE uses a database to store resources and other runtime data. You have the choice between a memory-based datatabase, a simple file-based database and a PostgreSQL database.

## TinyDB File-Based

The default database is a simple but fast file-based database using the [TinyDB](https://github.com/msiemens/tinydb){target=_new} library. By default, it requires no additional setup.

The database files are stored by default in the directory *{baseDirectory}/data* (which can be changed by a [configuration setting](../setup/Configuration-database.md#tinydb)). 

You enable the TinyDB database by setting the *databaseType* setting in the *\[basic.config\]* section to *tinydb*:

```ini title="Enable TinyDB as database"
[basic.config]
databaseType=tinydb
```

## TinyDB In-Memory

TinyDB also provides a memory-based database that might be useful for testing and development purposes, or if you want to start with a clean database each time you start the CSE.

You enable the in-memory database by setting the *databaseType* setting in the *\[basic.config\]* section to *memory*:

```ini title="Enable in-memory database"
[basic.config]
databaseType=memory
```


## PostgreSQL

An alternative to the file-based database is to use a PostgreSQL database. This requires a running PostgreSQL server to which the CSE can connect. The [PostgreSQL connection settings](../setup//Configuration-database.md#postgresql) are configured in the *acme.ini* configuration file.

The following steps describe how to set up a PostgreSQL database for the ACME CSE:

1. Optional: Install PostgreSQL on your system. You can download the installer from the [PostgreSQL website](https://www.postgresql.org/download/){target=_new}.
1. Create a new database and user for the CSE. It is recommended to use the CSE-ID as the database name and as the role name.  
For example, you can use the following commands to create a new database named *id-in* and a role named *id-in* with the password *acme*:

```bash title="Create database and role"
psql -c "CREATE DATABASE \"id-in\";"
psql -c "CREATE USER \"id-in\" WITH PASSWORD 'acme';"
psql -c "GRANT ALL PRIVILEGES ON DATABASE \"id-in\" TO \"id-in\";"
```

1. If not done during the setup procedure above: Edit the *acme.ini* configuration file and the following settings under the *\[database.postgresql\]* section:

	```ini title="PostgreSQL database settings"
		[database.postgresql]
		password = acme
	```

	All other settings are optional and can be left at their default values. The *database* and *role* settings are set to the CSE-ID by default. If you used different names for the database and role, you have to adjust these settings accordingly. Also the *host* and *port* settings are set to *localhost* and *5432* by default. If your PostgreSQL server is running on a different host or port, you have to adjust these settings as well.  
	You also need to enable the PostgreSQL database by setting the *databaseType* setting in the *\[basic.config\]* section to *postgresql*:

	```ini title="Enable postgreSQL database"
		[basic.config]
		databaseType=postgresql
	```

1. Run the CSE.  
The database schema, tables and other structures are created automatically by the CSE when it starts and connects for the first time. 


### Disabling PostgreSQL Support

Sometimes it may not be possible or desirable to use a PostgreSQL database, for example, when running the CSE on a system where PostgreSQL is not available or when you want to use the CSE in a simple test environment.

In this case, you can disable the PostgreSQL database by setting the *databaseType* setting in the *\[basic.config\]* section to *tinydb* or *memory*:

```ini title="Disable PostgreSQL database"
[basic.config]
databaseType=tinydb
```

In order to prevent the PostgreSQL Python modules (i.e. psycopg2) to be loaded you can also set the `ACME_NO_PGSQL` environment variable to any value before running the CSE:

```bash title="Disable PostgreSQL Database Support in Environment"
export ACME_NO_PGSQL=1
```
