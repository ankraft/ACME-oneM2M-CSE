# MQTT Requests

This directory contains a couple of shell scripts that sends MQTT requests to the CSE to test certain aspects.
These tests are intended  to be run manually.

## Installation

- The tests use the mqtt command line client from hivemq available at [https://github.com/hivemq/mqtt-cli](https://github.com/hivemq/mqtt-cli).
- The file [./config.sh](config.sh) contains a couple of configuration variables that are used to connect to an MQTT broker, the CSE etc.

## Running

Just run the tests on a command line:


	$ sh <script.sh>

Please note, that the scripts **don't** remove created resources. One must restart or reset the CSE.

