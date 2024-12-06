---
title: App SDK for Python - Getting Started
---

# App Functions SDK for Python - Getting Started

The SDK is built around the concept of a "Functions Pipeline". A functions pipeline is a collection of various functions that process the data in the defined order. The functions pipeline is executed by the specified [trigger](../details/Triggers.md) in the `configuration.yaml` . The initial function in the pipeline is called with the event that triggered the pipeline (ex. `dtos.Event`). Each successive call in the pipeline is called with the return result of the previous function. Let's take a look at a simple example that creates a pipeline to filter particular device ids and subsequently transform the data to XML:
```python
import asyncio
import os
from typing import Any, Tuple

from app_functions_sdk_py.contracts import errors
from app_functions_sdk_py.functions import filters, conversion
from app_functions_sdk_py.factory import new_app_service
from app_functions_sdk_py.interfaces import AppFunctionContext

service_key = "app-simple-filter-xml"

if __name__ == "__main__":
    # turn off secure mode for examples. Not recommended for production
    os.environ["EDGEX_SECURITY_SECRET_STORE"] = "false"

    # 1) First thing to do is to create a new instance of an EdgeX Application Service.
    service, result = new_app_service(service_key)
    if result is False:
        os._exit(-1)

    # Leverage the built-in logging service in EdgeX
    lc = service.logger()

    try:
        # 2) shows how to access the application's specific configuration settings.
        device_names = service.get_application_setting_strings("DeviceNames")
        lc.info(f"Filtering for devices {device_names}")
        # 3) This is our pipeline configuration, the collection of functions to execute every time an event is triggered.
        service.set_default_functions_pipeline(
            filters.new_filter_for(filter_values=device_names).filter_by_device_name,
            conversion.Conversion().transform_to_xml
        )
        # 4) Lastly, we'll go ahead and tell the SDK to "start" and begin listening for events to trigger the pipeline.
        asyncio.run(service.run())
    except Exception as e:
        lc.error(f"{e}")
        os._exit(-1)

    # Do any required cleanup here
    os._exit(0)

```

The above example is intended to simply demonstrate the structure of your application. It's important to note that the output of the final function is not accessible within the application itself. You must provide a function in order to work with the data from the previous function. Let's go ahead and add the following function that prints the output to the console.

```python
def print_xml_to_console(ctx: AppFunctionContext, data: Any) -> Tuple[bool, Any]:
    """
    Print the XML data to the console
    """
    # Leverage the built-in logging service in EdgeX
    if data is None:
        return False, errors.new_common_edgex(errors.ErrKind.CONTRACT_INVALID,"print_xml_to_console: No Data Received")

    if isinstance(data, str):
        print(data)
        return True, None
    return False, errors.new_common_edgex(errors.ErrKind.CONTRACT_INVALID,"print_xml_to_console: Data received is not the expected 'str' type")
```
After placing the above function in your code, the next step is to modify the pipeline to call this function:

```go
        # 3) This is our pipeline configuration, the collection of functions to execute every time an event is triggered.
        service.set_default_functions_pipeline(
            filters.new_filter_for(filter_values=device_names).filter_by_device_name,
            conversion.Conversion().transform_to_xml,
            print_xml_to_console
        )
```
Set the Trigger type to `http` in configuration file found here: [res/configuration.yaml](https://github.com/edgexfoundry/edgex-examples/blob/{{edgexversion}}/application-services/custom/simple-filter-xml/res/configuration.yaml)

```yaml 
Trigger:
  Type: http
```

Using PostMan or curl send the following JSON to `localhost:<port>/api/{{api_version}}/trigger`

```json
{
    "requestId": "82eb2e26-0f24-48ba-ae4c-de9dac3fb9bc",
    "apiVersion" : "{{api_version}}",
    "event": {
        "apiVersion" : "{{api_version}}",
        "deviceName": "Random-Float-Device",
        "profileName": "Random-Float-Device",
        "sourceName" : "Float32",
        "origin": 1540855006456,
        "id": "94eb2e26-0f24-5555-2222-de9dac3fb228",
        "readings": [
            {
                "apiVersion" : "{{api_version}}",
                "resourceName": "Float32",
                "profileName": "Random-Float-Device",
                "deviceName": "Random-Float-Device",
                "value": "76677",
                "origin": 1540855006469,
                "valueType": "Float32",
                "id": "82eb2e36-0f24-48aa-ae4c-de9dac3fb920"
            }
        ]
    }
}
```

After making the above modifications, you should now see data printing out to the console in XML when an event is triggered.

!!! note
    You can find more examples located in the [examples](https://github.com/IOTechSystems/app-functions-sdk-python/tree/main/examples) section.

Up until this point, the pipeline has been triggered by an event over HTTP and the data at the end of that pipeline lands in the last function specified. In the example, data ends up printed to the console. Perhaps we'd like to send the data back to where it came from. In the case of an HTTP trigger, this would be the HTTP response. In the case of  EdgeX MessageBus, this could be a new topic to send the data back to the MessageBus for other applications that wish to receive it. To do this, simply call `ctx.set_response_data(data)` passing in the data you wish to "respond" with. In the above `print_xml_to_console(...)` function, replace `print(data)` with `ctx.set_response_data(data)`. You should now see the response in your postman window when testing the pipeline.

!!! note
    The App Functions SDK contains a quick start template for creating new custom application services. See [https://github.com/IOTechSystems/app-functions-sdk-python/blob/main/app-service-template/README.md](https://github.com/IOTechSystems/app-functions-sdk-python/blob/main/app-service-template/README.md) 
