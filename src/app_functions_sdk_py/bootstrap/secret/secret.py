#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0
import threading
from dataclasses import dataclass

from ..container.logging import logging_client_from
from ..container.secret import SecretProviderName, SecretProviderExtName
from ..di.container import Container
from ...bootstrap import environment
from ...bootstrap.interface.secret import SecretProviderExt
from ...bootstrap.secret.insecure import InsecureProvider
from ...bootstrap.timer import Timer
from ...internal.common.config import ConfigurationStruct


@dataclass
class SecretData:
    """
    Represents the data of secrets.
    """
    username: str
    password: str
    key_pem_block: str
    cert_pem_block: str
    ca_pem_block: str


def new_secret_provider(configuration: ConfigurationStruct, ctx: threading.Event,
                        startup_timer: Timer, dic: Container, service_key: str) -> SecretProviderExt:
    """
    Creates a new fully initialized the Secret Provider.
    """
    lc = logging_client_from(dic.get)
    provider = None

    if environment.use_security_secret_store(lc):
        # TODO: Implement Secure Provider in milestone E  # pylint: disable=fixme
        pass
    else:
        provider = InsecureProvider(configuration, lc, dic)

    dic.update({
        SecretProviderName: lambda get: provider,
        SecretProviderExtName: lambda get: provider
    })

    return provider
