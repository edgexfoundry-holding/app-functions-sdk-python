# Application Service Template

This folder contains a buildable/runnable sample for a new custom application service based on the release of the App Functions Python SDK.

This sample application service--**app-new-service**--is configured with default Message Bus trigger to subscribe for any event messages published to EdgeX message bus, and process these event messages with the default pipeline containing two functions: `filter_by_device_name` and `mqtt_send`, so the app service will only process event messages coming from **Random-Integer-Device**, and then republish such event messages to an external MQTT broker **test.mosquitto.org** via **test_topic** topic.

Follow the instructions below to try this sample application service:

1. Prepare your local development environment with following dependencies:
   - python 3.10 or above
   - docker
   - make
   - git

2. As the app service will use default Message Bus trigger to consume events from EdgeX MessageBus, we have to run up EdgeX core services and device-virtual service to simulate the EdgeX events in your local environment. The easiest way to run up EdgeX services is through script available from https://github.com/edgexfoundry/edgex-compose:
   - `git clone https://github.com/edgexfoundry/edgex-compose.git`
   - switch into the `edgex-compose/compose-builder` directory
   - `make run no-secty ds-virtual mqtt-bus keeper`

3. By the completion of above step, you will have EdgeX core services, device-virtual service, and an MQTT broker running as docker container in your local environment, and you can examine their running status by using command: `docker ps -a`. Note that the running device-virtual service will periodically generate EdgeX events and publish them to EdgeX message bus, and you can observe those EdgeX events by using following command:
   - `docker exec edgex-mqtt-broker mosquitto_sub -v -t 'edgex/events/#'`

4. Now we have EdgeX services up and running, the next step is to copy contents of this repository to your local environment by using following command:
   - `git clone https://github.com/IOTechSystems/app-functions-sdk-python.git`

5. Switch into the `app-functions-sdk-python` directory

6. Examine the code of `app-service-template/main.py` to understand how to write a custom application service using the App Functions Python SDK.

7. Create a virtual environment in the root of the repository in your local environment:
   - `python3 -m venv venv`

8. Switch to the virtual environment:
   - `source ./venv/bin/activate`

9. Install the dependencies for the App Functions Python SDK in the virtual environment:
   - `pip install -r requirements.txt`

10. Install the App Functions Python SDK in the virtual environment:
    - `pip install -e .`

11. Switch into the app-service-template directory and run the main.py.  Note that we specify the common configuration file to use with the `-cc` flag.
    - `cd app-service-template`
    - `python main.py -cc ./res/common-configuration.yaml`

12. Once the app-new-service is running, it will consume EdgeX events from the EdgeX message bus, filter for events coming from **Random-Integer-Device**, and then re-publish the events to an external MQTT broker **test.mosquitto.org** via **test_topic** topic. To observe those events being published to **test.mosquitto.org**, you can use following command:
    - `docker exec edgex-mqtt-broker mosquitto_sub -v -t 'test_topic' -h test.mosquitto.org`

13. To stop the app-new-service, you can press `Ctrl+C` to stop the running process.
