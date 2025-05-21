# Zookeeper Tool

This tool is used to simplify the process of creating and managing Zookeeper nodes that contain ACME configuration data. It provides a command-line interface for creating, deleting, and listing nodes in Zookeeper as well as to store and retriebe configuration data in INI format.

## Running the Tool

To run the tool, use the following command:

```bash
python zk-tool.py <command> [options]
```

The available commands are:

```
usage: zk-tool.py [-h] [--zookeeper-host hostname] [--zookeeper-port port] [--zookeeper-root nodeName]
                  [--verbose] [--case-sensitive] [--config filename] [--config-default filename]
                  [--store-config | --store-config-all | --retrieve-config] [--list [path] | --add
                  keyPath value | --update keyPath value | --DELETE keyPath]

options:
  -h, --help            show this help message and exit
  --zookeeper-host hostname, -host hostname
                        hostname of the Zookeeper server (default: localhost)
  --zookeeper-port port, -port port
                        port of the Zookeeper server (default: 2181)
  --zookeeper-root nodeName, -root nodeName
                        name of the configuration node (default: /acme)
  --verbose, -v         enable verbose output
  --case-sensitive, -cs
                        enable case sensitive node and key names (default: False)

ACME CSE configuration operations:
  --config filename, -c filename
                        specify the ACME CSE's instance configuration file (default: ../../acme.ini)
  --config-default filename, -cd filename
                        specify the ACME CSE' default configuration file (default:
                        ../../acme/init/acme.ini.default)
  --store-config, -store
                        store individual ACME CSE configuration in Zookeeper
  --store-config-all    store all (incl. defaults) ACME CSE configuration in Zookeeper
  --retrieve-config, -retrieve
                        retrieve ACME CSE configuration from Zookeeper

Zookeeper basic operations:
  --list [path], -ls [path]
                        list contents of a Zookeeper node (optional: specify path to list, defaults to
                        root node)
  --add keyPath value, -a keyPath value
                        add a key-value pair to a Zookeeper node
  --update keyPath value, -u keyPath value
                        update a key-value pair
  --DELETE keyPath      delete a key-value pair

```

> Note, that as a default, all node and key names are case insensitive. To enable case sensitivity, use the `--case-sensitive` option.


## Example Usage

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

> Note, the --DELETE command deletes the specified key-value pair and all its children from the Zookeeper server. Use with caution.


