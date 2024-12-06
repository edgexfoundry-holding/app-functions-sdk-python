#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0


import threading

from ...registry.config import Config
from ..interface.secret import SecretProviderExt
from ..timer import Timer
from ...contracts.clients.logger import Logger
from ...contracts import errors
from ...contracts.common.constants import API_PING_ROUTE
from ...internal.common.config import ConfigurationStruct
from ...registry.factory import new_registry_client
from ...registry.interface import Client


def create_registry_client(service_key: str, service_config: ConfigurationStruct,
                           secret_provider: SecretProviderExt, lc: Logger) -> Client:
    """
    Creates and returns a registry.Client instance.
    """
    access_token = None

    # secret_provider will be none if not configured to be used.
    # In that case, no access token required.
    if secret_provider is not None:
        def get_access_token():
            # Define the callback function to retrieve the Access Token
            try:
                token = secret_provider.get_access_token(
                    service_config.Registry.Type, service_key)
                lc.info(f"Using Registry access token of length {len(token)}")
                return token
            except errors.EdgeX as e:
                raise errors.new_common_edgex_wrapper(e)

        try:
            access_token = get_access_token()
        except errors.EdgeX as err:
            raise errors.new_common_edgex_wrapper(err)

    if (len(service_config.Registry.Host) == 0 or service_config.Registry.Port == 0 or
            len(service_config.Registry.Type) == 0):
        raise errors.new_common_edgex(errors.ErrKind.CONTRACT_INVALID,
                                      "Registry configuration is empty or incomplete. "
                                      "Missing common config? "
                                      "Use -cp or -cc flags for common config.")

    registry_config = Config(
        host=service_config.Registry.Host,
        port=service_config.Registry.Port,
        service_type=service_config.Registry.Type,
        access_token=access_token,
        service_key=service_key,
        service_host=service_config.Service.Host,
        service_port=service_config.Service.Port,
        service_protocol='http',
        check_interval=service_config.Service.HealthCheckInterval,
        check_route=API_PING_ROUTE,
        auth_injector=None  # TODO: Implement Secret Provider at milestone E  # pylint: disable=fixme

    )

    lc.info(f"Using Registry ({registry_config.service_key}) from {registry_config.get_registry_url()}")
    return new_registry_client(registry_config)


def register_with_registry(ctx_done: threading.Event, startup_timer: Timer, config: ConfigurationStruct, lc: Logger, service_key: str, secret_provider):
    """
    Connects to the registry and registers the service with the Registry.
    """

    def register(client: Client):
        if not client.is_alive():
            raise errors.new_common_edgex(errors.ErrKind.SERVICE_UNAVAILABLE, "registry is not available")
        try:
            client.register()
        except errors.EdgeX as e:
            raise errors.new_common_edgex_wrapper(e)

    try:
        registry_client = create_registry_client(service_key, config, secret_provider, lc)
    except errors.EdgeX as e:
        raise errors.new_common_edgex_wrapper(e)

    while startup_timer.has_not_elapsed():
        try:
            register(registry_client)
            return registry_client
        except errors.EdgeX as e:
            lc.warn(str(e))
            if ctx_done.is_set():
                raise errors.EdgeX(errors.ErrKind.SERVER_ERROR, "aborted RegisterWithRegistry()")
            startup_timer.sleep_for_interval()
    raise errors.EdgeX(errors.ErrKind.SERVER_ERROR, "unable to register with Registry in allotted time")
