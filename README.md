# Application Functions SDK for Python

The EdgeXFoundry Application Functions Software Development Kit (SDK) for Python. This is a Python para SDK for the [app-functions-sdk-go](https://github.com/edgexfoundry/app-functions-sdk-go), which is designed to help you create EdgeX application services that can process/transform/export data from EdgeX.

## Prerequisites

This Python SDK is supported on Python 3.10 or later.

## File Structure

This Python SDK is designed to follow the file structure that can be installed by [pip package installer](https://pypi.org/project/pip/) as a Python package **app_functions_sdk_py**. 

The file structure of this Python SDK is as follows:
- [app-service-template](./app-service-template): this folder contains a template for creating a new EdgeX application service using this Python SDK.
- [src/app_functions_sdk_py](./src/app_functions_sdk_py): this folder contains the source code of the Python SDK with top-level package **app_functions_sdk_py**, which is further divided into the following subpackages:
- [app_functions_sdk_py](./src/app_functions_sdk_py): this subpackage contains modules for implementation of the Python SDK.
  - [boostrap](./src/app_functions_sdk_py/bootstrap): this subpackage contains modules for implementation of the bootstrap library for service bootstrap. 
  - [clients](./src/app_functions_sdk_py/clients): this subpackage contains modules for implementation of various client libraries that are similar to https://github.com/edgexfoundry/go-mod-core-contracts/tree/main/clients.
  - [configuration](./src/app_functions_sdk_py/configuration): this subpackage contains modules for implementation of configuration client library that are similar to https://github.com/edgexfoundry/go-mod-configuration.
  - [contracts](./src/app_functions_sdk_py/contracts): this subpackage contains modules for implementation of contract models that are similar to https://github.com/edgexfoundry/go-mod-core-contracts.
  - [functions](./src/app_functions_sdk_py/functions): this subpackage contains modules for implementation of functions that can be used to process/transform/export data from EdgeX.
  - [interfaces](./src/app_functions_sdk_py/interfaces): this subpackage contains modules for various abstract class definition of a role or contract that can be fulfilled by any class or struct that inherits the abstract class. These abstract classes are defined to promote flexibility and decoupling in this SDK. 
  - [internal](./src/app_functions_sdk_py/internal): this subpackage contains modules for internal implementation of the SDK. These modules are not intended to be used by the end user.
  - [messaging](./src/app_functions_sdk_py/messaging): this subpackage contains modules for implementation of messaging client library that are similar to https://github.com/edgexfoundry/go-mod-messaging.
  - [registry](./src/app_functions_sdk_py/registry): this subpackage contains modules for implementation of registry client library that are similar to https://github.com/edgexfoundry/go-mod-registry.
  - [utils](./src/app_functions_sdk_py/utils): this subpackage contains utility functionality.
- [tests](./tests): this folder contains the unit tests for the Python SDK. Any new unit-tests should be added here with corresponding file structure as to src/app_functions_sdk_py.
- [setup.py](./setup.py): this file is used to package the Python SDK into a Python package. This file is used to dynamically specify the package version.
- [pyproject.toml](./pyproject.toml): this file is used to specify the build system requirements for the Python SDK.
- [Makefile](./Makefile): the Makefile used to build and test the Python SDK.
- [requirements.txt](./requirements.txt): this file specifies the dependencies required to build and test the Python SDK.

## Features Supported

This Python SDK aims to facilitate the development for a python developer to create their own EdgeX Application Service with following features:
- Basic logging mechanism
- Load and apply the EdgeX environment variables
- Consume configuration from YAML configuration file
- Consume configuration from EdgeX Keeper
- Process incoming data from EdgeX Message Bus via either MQTT or NATS-Core
- Process incoming data from a HTTP POST request
- Basic EdgeX common REST API, such as ping, version, and config

The SDK also provides the following built-in functions to process/transform/export data from EdgeX:

- [Filtering functions](./src/app_functions_sdk_py/functions/filter.py) to filter data based on profile name, source name, device name, or resource name
- [MQTT Export function](./src/app_functions_sdk_py/functions/mqtt.py) to export data to an external MQTT broker
- [Batch functions](./src/app_functions_sdk_py/functions/batch.py) to batch data based on the number of events or the time window
- [Compression functions](./src/app_functions_sdk_py/functions/compression.py) to compress data
- [Data protection functions](./src/app_functions_sdk_py/functions/aesprotection.py) to encrypt data
- [Conversion functions](./src/app_functions_sdk_py/functions/conversion.py) to convert data from one format to another
- [JSONLogic function](./src/app_functions_sdk_py/functions/jsonlogic.py) to process data based on JSONLogic rules
- [Set response function](./src/app_functions_sdk_py/functions/responsedata.py) to set the response data into passed in event that received from previous function
- [Wrap into event function](./src/app_functions_sdk_py/functions/wrap_into_event.py) to create an EventRequest using the Event/Reading metadata that have been set

## Run Tests

To run the unit-tests against SDK, you will have to follow steps as described below:

1. Create a virtual environment in the root of the repository in your local environment:
   - `python3 -m venv venv`

2. Switch to the virtual environment:
   - `source ./venv/bin/activate`

3. Install the dependencies for the App Functions Python SDK in the virtual environment:
   - `pip install -r requirements.txt`

4. Install the App Functions Python SDK in the virtual environment:
   - `make install-sdk`

5. Run the tests against the SDK by using the following command:
   - `make test-sdk`

## Try the sample application service

To further understand the usage of this Python SDK, you can try the sample application service provided in the [app-service-template](./app-service-template) folder. This sample application service is configured with default Message Bus trigger to subscribe for any event messages published to EdgeX message bus, and process these event messages with the default pipeline containing two functions: `filter_by_device_name` and `mqtt_send`, so the app service will only process event messages coming from **Random-Integer-Device**, and then republish such event messages to an external MQTT broker **test.mosquitto.org** via **test_topic** topic.
