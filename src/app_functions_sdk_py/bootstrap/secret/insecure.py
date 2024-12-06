#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0
#  """
#  This module provides the classes and functions for InsecureProvider
#  """
from datetime import datetime
from typing import Callable, List, Any, Dict

from .constants import WILDCARD_NAME, SECRETS_REQUESTED_METRIC_NAME, SECRETS_STORE_METRIC_NAME
from ..config.config import get_insecure_secret_name_full_path, get_insecure_secret_data_full_path
from ..container.configuration import config_client_from
from ..di.container import Container
from ..interface.secret import SecretProviderExt, Secrets
from ...contracts.clients.logger import Logger
from ...contracts import errors
from ...internal.common.config import ConfigurationStruct, InsecureSecretsInfo


class InsecureProvider(SecretProviderExt):
    """ InsecureProvider access the secrets from the configuration """

    def __init__(self, config: ConfigurationStruct, lc: Logger, dic: Container):
        self.config = config
        self.lc = lc
        self.last_updated = datetime.now()
        self.registered_secret_callbacks: Dict[str, Callable[[str], None]] = {}
        self.security_secrets_requested = Any  # TODO: Implement Metrics in milestone D  # pylint: disable=fixme
        self.security_secrets_stored = Any
        self.dic = dic

    def get_secrets(self, secret_name: str, *secret_keys: str) -> Secrets:
        """
        Retrieves secrets from an Insecure Secrets secret store.
        secret_name specifies the type or location of the secrets to retrieve.
        secret_keys specifies the secrets which to retrieve. If no keys are provided then all the keys
        associated with the specified secretName will be returned.
        """
        # TODO: Implement Metrics in milestone D  # pylint: disable=fixme
        # self.security_secrets_requested.inc(1)

        results = Secrets()
        secret_name_exists = False
        missing_keys = []

        insecure_secrets = self.config.Writable.InsecureSecrets
        if insecure_secrets is None:
            raise errors.new_common_edgex(errors.ErrKind.ENTITY_DOES_NOT_EXIST,
                                          "InsecureSecrets missing from configuration")

        for _, insecure_secret in insecure_secrets.items():
            if insecure_secret.SecretName == secret_name:
                if len(secret_keys) == 0:
                    # If no keys are provided then all the keys associated with the specified
                    # secretName will be returned
                    results.update(insecure_secret.SecretData)
                    return results

                secret_name_exists = True
                for key in secret_keys:
                    if key not in insecure_secret.SecretData:
                        missing_keys.append(key)
                        continue
                    results[key] = insecure_secret.SecretData[key]

        if len(missing_keys) > 0:
            raise errors.new_common_edgex(errors.ErrKind.ENTITY_DOES_NOT_EXIST,
                                          f"No value for the keys: "
                                          f"[{', '.join(missing_keys)}] exists")

        if not secret_name_exists:
            raise errors.new_common_edgex(errors.ErrKind.ENTITY_DOES_NOT_EXIST,
                                          f"Error, secretName ({secret_name}) "
                                          f"doesn't exist in secret store")

        return results

    def store_secrets(self, secret_name: str, secrets: Secrets):
        """
        Attempts to store the secrets in the ConfigurationProvider's InsecureSecrets.
        If no ConfigurationProvider is in use, it will return an error.
        Note: This does not call SecretUpdatedAtSecretName, SecretsUpdated, or increase the
        secrets stored metric because those will all occur once the ConfigurationProvider tells
        the service that the configuration has updated.
        """
        config_client = config_client_from(self.dic.get)
        if config_client is None:
            raise errors.new_common_edgex(
                errors.ErrKind.NOT_ALLOWED,
                "can't store secrets. ConfigurationProvider is not in use or has not been "
                "properly initialized",
                None
            )

        # insert the top-level data about the secret name
        try:
            config_client.put_configuration_value(get_insecure_secret_name_full_path(secret_name),
                                                  secret_name.encode())
        except errors.EdgeX as err:
            raise errors.new_common_edgex(
                errors.ErrKind.COMMUNICATION_ERROR,
                "error setting secretName value in the config provider",
                err
            )

        # insert each secret key/value pair
        for key, value in secrets.items():
            try:
                config_client.put_configuration_value(get_insecure_secret_data_full_path(secret_name, key),
                                                      value.encode())
            except errors.EdgeX as err:
                raise errors.new_common_edgex(
                    errors.ErrKind.COMMUNICATION_ERROR,
                    "error setting secretData key/value pair in the config provider",
                    err
                )

    def secrets_updated(self):
        """
        Resets LastUpdate time for the Insecure Secrets.
        """
        self.last_updated = datetime.now()

    def secrets_last_updated(self) -> datetime:
        """
        Returns the last time insecure secrets were updated
        """
        return self.last_updated

    def get_access_token(self, _, __) -> str:
        """
        Returns the AccessToken for the specified type, which in insecure mode is not need
        so just returning an empty token.
        """
        return ""

    def has_secret(self, secret_name: str) -> bool:
        """
        Returns true if the service's SecretStore contains a secret at the specified secretName.
        """
        insecure_secrets = self.config.Writable.InsecureSecrets
        if insecure_secrets is None:
            raise errors.new_common_edgex(errors.ErrKind.ENTITY_DOES_NOT_EXIST,
                                          "InsecureSecrets missing from configuration")

        for _, insecure_secret in insecure_secrets.items():
            # TODO: Find out why insecure_secret is a dict and not an InsecureSecretsInfo object.  # pylint: disable=fixme
            s = InsecureSecretsInfo(**insecure_secret)
            if s.SecretName == secret_name:
                return True

        return False

    def list_secret_names(self) -> List[str]:
        insecure_secrets = self.config.Writable.InsecureSecrets
        if insecure_secrets is None:
            raise errors.new_common_edgex(errors.ErrKind.ENTITY_DOES_NOT_EXIST,
                                          "InsecureSecrets missing from configuration")

        return [secret.SecretName for _, secret in insecure_secrets.items()]

    def register_secret_update_callback(self, secret_name: str, callback: Callable[[str], None]):
        if secret_name in self.registered_secret_callbacks:
            raise errors.new_common_edgex(errors.ErrKind.DUPLICATE_NAME,
                                          f"there is a callback already registered for secretName "
                                          f"'{secret_name}'")

        # Register new call back for secretName.
        self.registered_secret_callbacks[secret_name] = callback

    def secret_updated_at_secret_name(self, secret_name: str):
        """
        Performs updates and callbacks for an updated secret or secretName.
        """
        # TODO: Implement Metrics in milestone D  # pylint: disable=fixme
        # self.security_secrets_stored.inc(1)

        self.last_updated = datetime.now()

        if not self.registered_secret_callbacks:
            return

        # Execute Callback for provided secretName.
        if secret_name in self.registered_secret_callbacks:
            self.lc.debug("invoking callback registered for secretName: '%s'", secret_name)
            self.registered_secret_callbacks[secret_name](secret_name)
        elif WILDCARD_NAME in self.registered_secret_callbacks:
            self.lc.debug("invoking wildcard callback for secretName: '%s'", secret_name)
            self.registered_secret_callbacks[WILDCARD_NAME](secret_name)

    def deregister_secret_update_callback(self, secret_name: str):
        """
        Removes a secret's registered callback secretName.
        """
        del self.registered_secret_callbacks[secret_name]

    def get_metrics_to_register(self) -> Dict[str, Any]:
        """
        Returns all metric objects that needs to be registered.
        """
        return {
            SECRETS_REQUESTED_METRIC_NAME: self.security_secrets_requested,
            SECRETS_STORE_METRIC_NAME: self.security_secrets_stored
        }

    def get_self_jwt(self) -> str:
        """
        Returns an encoded JWT for the current identity-based secret store token
        """
        # If security is disabled, return an empty string.
        # It is presumed HTTP invokers will not add an authorization token that is empty to
        # outbound requests.
        return ""

    def is_jwt_valid(self, jwt: str) -> bool:
        """
        Evaluates a given JWT and returns a true/false if the JWT is valid
        (i.e. belongs to us and current) or not.
        """
        return True

    def http_transport(self):
        """
        Returns the http.RoundTripper to be used by http-based clients.
        """
        # TODO: Find the equivalent to http.RoundTripper in Python.  # pylint: disable=fixme
        pass

    def set_http_transport(self, _):
        """
        Sets the http.RoundTripper to be used by http-based clients.
        """
        # empty on purpose

    def is_zero_trust_enabled(self) -> bool:
        """
        Returns whether zero trust principles are enabled.
        """
        return False

    def enable_zero_trust(self):
        """
        Marks the provider as being zero trust enabled
        """
        # empty on purpose
