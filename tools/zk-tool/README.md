# Zookeeper Tool

This tool is used to simplify the process of creating and managing [Apache Zookeeper](https://zookeeper.apache.org/){target=_new} nodes that contain ACME configuration data. It provides a command-line interface for creating, updating, deleting, and listing nodes in Zookeeper as well as to store and retriebe configuration data in INI format.

## Running the Tool

To run the tool, run the following command in the `tools/zk-tool` directory:

```bash
python zk-tool.py <command> [options]
```

The available commands are:

| Option / Command                         | Short Option(s) | Description                                                                                  | Default Value                          |
|------------------------------------------|-----------------|----------------------------------------------------------------------------------------------|----------------------------------------|
| `--help`                                 | `-h`            | Show this help message and exit                                                              |                                        |
| `--zookeeper-host hostname`              | `-host`         | Hostname of the Zookeeper server                                                             | `localhost`                            |
| `--zookeeper-port port`                  | `-port`         | Port of the Zookeeper server                                                                 | `2181`                                 |
| `--zookeeper-root nodeName`              | `-root`         | Name of the configuration node                                                               | `/acme`                                |
| `--verbose`                              | `-v`            | Enable verbose output                                                                        |                                        |
| `--case-sensitive`                       | `-cs`           | Enable case sensitive node and key names                                                     | `False`                                |
| `--config filename`                      | `-c`            | Specify the ACME CSE's instance configuration file                                           | `../../acme.ini`                       |
| `--config-default filename`              | `-cd`           | Specify the ACME CSE's default configuration file                                            | `../../acme/init/acme.ini.default`     |
| `--store-config`                         | `-store`        | Store individual ACME CSE configuration in Zookeeper                                         |                                        |
| `--store-config-all`                     |                 | Store all (incl. defaults) ACME CSE configuration in Zookeeper                               |                                        |
| `--retrieve-config`                      | `-retrieve`     | Retrieve ACME CSE configuration from Zookeeper                                               |                                        |
| `--list [path]`                          | `-ls`           | List contents of a Zookeeper node (optional: specify path to list, defaults to root node)    |                                        |
| `--add keyPath value`                    | `-a`            | Add a key-value pair to a Zookeeper node                                                     |                                        |
| `--update keyPath value`                 | `-u`            | Update a key-value pair                                                                      |                                        |
| `--DELETE keyPath`                       |                 | Delete a key-value pair                                                                      |                                        |


Key paths are specified as a relative path to the root node. 
For example, the key path `http/security/usetls` is relative to the root node `/id-in` and will be stored
in Zookeeper as `/id-in/http/security/usetls`.

Key pathes are case-insensitive by default. This means that all keys are stored in lowercase and the
key path is converted to lowercase before storing it in Zookeeper. 
This is sone to ensure that the keys are always stored in a consistent format and to avoid issues with
the case-insentive nature of the INI configuration files.  
To enable case-sensitive key paths, use the `--case-sensitive` option.

## Example Usage

The name of the root node for the configuration on the Zookeeper server in the following examples is `/id-in`. 


### Store Configuration

To store an individual ACME CSE configuration from a local *acme.ini* file in a Zookeeper server, use the following command:

```bash
python zk-tool.py -host zookeeper.example.com -root /id-in -store
```

### Retrieve Configuration

To retrieve the configuration from Zookeeper and print it to *stdout*, use the following command:

```bash
python zk-tool.py -host zookeeper.example.com -root /id-in -retrieve
```

### List Zookeeper Nodes

To list the contents of a Zookeeper node, use the following command:

```bash
python zk-tool.py -host zookeeper.example.com -root /id-in -ls
```

To list the contents of a specific section (e.g. *\[http.security]* ), specify the path as follows:

```bash
python zk-tool.py -host zookeeper.example.com -root /id-in -ls http/security
```

### Add a Key-Value Pair

To add a key-value pair to a Zookeeper node, use the following command:

```bash
python zk-tool.py -host zookeeper.example.com -root /id-in -a http/security/usetls true
```

### Update a Key-Value Pair

To update a key-value pair in a Zookeeper node, use the following command:

```bash
python zk-tool.py -host zookeeper.example.com -root /id-in -u http/security/usetls false
```

### Delete a Key-Value Pair

To delete a key-value pair from a Zookeeper server, use the following command:

```bash
python zk-tool.py -host zookeeper.example.com -root /id-in -DELETE http/security/usetls
```

!!! Attention

	The --DELETE command deletes the specified key-value pair and all its children from the Zookeeper server. Use with caution.
