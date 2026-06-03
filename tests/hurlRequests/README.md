# hurl Requests

This directory contains a collection of [hurl](https://hurl.dev/) request files for testing the CSE and providing examples of how to use various oneM2M features. 

[hurl](https://hurl.dev/) is a command-line tool for running HTTP requests defined in a simple text format. It allows you to easily test APIs and automate interactions with web services. It can also be used to run performance tests and validate API responses.


## Running the tests

[hurl](https://hurl.dev/) uses an environment variable file to configure the target host, port, scheme and other parameters. 

The file `hurl.env.dist` serves as a template for creating your own `hurl.env` file. You should copy `hurl.env.dist` to `hurl.env` and then edit the values in `hurl.env` to match your CSE configuration.

Once you have your `hurl.env` file configured, you can run the tests using the following command:

```bash
hurl --variables-file hurl.env retrieveCSEBase.hurl
```

This command will execute the requests defined in `retrieveCSEBase.hurl` using the variables from `hurl.env`. You can replace `retrieveCSEBase.hurl` with any of the other `.hurl` files in this directory to run different tests.

The output will show the body of the last request. To prevent this you can add `--no-output` to the command:

```bash
hurl --variables-file hurl.env --no-output retrieveCSEBase.hurl
```

To enable "test mode" which will run the requests in a different mode, you can add `--test` to the command:

```bash
hurl --variables-file hurl.env --test retrieveCSEBase.hurl
```

To run a command file multiple times, you can use the `--repeat` option together with `--test`:

```bash
hurl --variables-file hurl.env --test --repeat 1000  retrieveCSEBase.hurl
```

In this case you can also add `--jobs` to specify the number of requests to run in parallel:

```bash
hurl --variables-file hurl.env --test --repeat 1000 --jobs 200 retrieveCSEBase.hurl
```

## Authentication

To use authentication, you can add the `authorization` variable to your `hurl.env` file. This variable can contain a Basic string or a Bearer token, depending on the authentication method you are using.

## Further reading

For more information on how to use hurl and its features, please refer to the official documentation:  [hurl documentation](https://hurl.dev/docs/manual.html)