#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0
"""
This module provides the classes and functions for AESProtection
"""
import base64
from typing import Tuple, Any, Optional

from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import pad, unpad
from Cryptodome.Hash import HMAC, SHA256

from ..contracts import errors
from ..contracts.common.constants import CONTENT_TYPE_TEXT
from ..interfaces import AppFunctionContext
from ..utils.helper import coerce_type

ALGORITHM = "algorithm"
ENCRYPT_AES256 = "aes256"
SECRET_NAME = "secretname"
SECRET_VALUE_KEY = "secretvaluekey"


class AESProtection:
    """ AESProtection encrypt the data with aes256 algorithm """

    def __init__(self, secret_name: str, secret_value_key: str):
        self.secret_name = secret_name
        self.secret_value_key = secret_value_key

    def encrypt(self, ctx: AppFunctionContext, data: Any) -> Tuple[bool, Any]:
        """ Encrypt encrypts a string, []byte, or json.Marshaller type using AES 256 encryption.
        It also signs the data using a SHA256 hash.
        It will return a Base64 encode []byte of the encrypted data. """
        if data is None:
            return False, errors.new_common_edgex(
                errors.ErrKind.SERVER_ERROR,
                f"function Encrypt in pipeline '{ctx.pipeline_id()}': No Data Received")

        ctx.logger().debug(f"Encrypting with AES256 in pipeline '{ctx.pipeline_id()}'")

        byte_data, err = coerce_type(data)
        if err is not None:
            return False, errors.new_common_edgex_wrapper(err)

        key, err = self.get_key(ctx)
        if err is not None:
            return False, errors.new_common_edgex_wrapper(err)

        # since PyCrypto 2.x is unmaintained, obsolete, and contains security vulnerabilities.
        # see https://github.com/pycrypto/pycrypto
        # use pycryptodome instead, refer to
        #   - https://github.com/Legrandin/pycryptodome
        #   - https://www.pycryptodome.org/src/cipher/modern#ccm-mode
        #   - https://www.pycryptodome.org/src/examples#encrypt-data-with-aes

        aes_key = key[0:32]
        hmac_key = key[-32:]
        cipher = AES.new(aes_key, AES.MODE_CCM)
        ct_bytes = cipher.encrypt(pad(byte_data, AES.block_size))
        hmac = HMAC.new(hmac_key, digestmod=SHA256)
        tag = hmac.update(cipher.nonce + ct_bytes).digest()

        # this output combination can refer to the app-functions-sdk-go
        # https://github.com/edgexfoundry/app-functions-sdk-go/blob/4c660cc5313959eaa6fb5d4a00bb7923fcfb4b46/internal/etm/etm.go#L132-L136
        res = cipher.nonce + ct_bytes + tag

        try:
            encoded = base64.b64encode(res)
        except (ValueError, TypeError) as e:
            return False, errors.new_common_edgex(
                errors.ErrKind.SERVER_ERROR,
                f"failed to encode encrypt data to base64 in pipeline '{ctx.pipeline_id()}'", e)

        # clear key
        key = bytes()

        ctx.set_response_content_type(CONTENT_TYPE_TEXT)

        return True, encoded

    def decrypt(self, ctx: AppFunctionContext, data: Any) -> Tuple[bool, Any]:
        """ Decrypt decrypts AES 256 encryption data. """
        if data is None:
            return False, errors.new_common_edgex(
                errors.ErrKind.SERVER_ERROR,
                f"function Encrypt in pipeline '{ctx.pipeline_id()}': No Data Received")

        ctx.logger().debug(f"Encrypting with AES256 in pipeline '{ctx.pipeline_id()}'")

        byte_data, err = coerce_type(data)
        if err is not None:
            return False, errors.new_common_edgex_wrapper(err)

        key, err = self.get_key(ctx)
        if err is not None:
            return False, errors.new_common_edgex_wrapper(err)

        aes_key = key[0:32]
        hmac_key = key[-32:]

        try:
            base64_decoded = base64.b64decode(byte_data)

            tag = base64_decoded[-32:]
            # the library creates a 11 bytes random nonce
            nonce = base64_decoded[0:11]
            ciphertext = base64_decoded[11:-32]

            HMAC.new(hmac_key, digestmod=SHA256).update(nonce + ciphertext).verify(tag)

            cipher = AES.new(aes_key, AES.MODE_CCM, nonce=nonce)
            decoded_data = unpad(cipher.decrypt(ciphertext), AES.block_size)
            ctx.set_response_content_type(CONTENT_TYPE_TEXT)
            key = bytes()
            return True, decoded_data
        except (ValueError, KeyError) as e:
            return False, errors.new_common_edgex(
                errors.ErrKind.SERVER_ERROR,
                f"Incorrect decryption in pipeline '{ctx.pipeline_id()}'", e)

    def get_key(self, ctx: AppFunctionContext) -> Tuple[bytes, Optional[errors.EdgeX]]:
        """ get_key gets secret key from the secret store """
        # If using Secret Store for the encryption key
        if len(self.secret_name) != 0 and len(self.secret_value_key) != 0:
            # Note secrets are cached so this call doesn't result in unneeded calls to
            # SecretStore Service and the cache is invalidated when StoreSecrets is used.
            secret_data = (ctx.secret_provider()
                           .get_secrets(self.secret_name, self.secret_value_key))

            if self.secret_value_key not in secret_data:
                return bytes(), errors.new_common_edgex(
                    errors.ErrKind.SERVER_ERROR,
                    f"unable find encryption key in secret data "
                    f"for name={self.secret_name} in pipeline '{ctx.pipeline_id()}' ")

            key = secret_data[self.secret_value_key]

            ctx.logger().debug(
                "Using encryption key from Secret Store at SecretName=%s & SecretValueKey=%s "
                "in pipeline '%s'",
                self.secret_name,
                self.secret_value_key,
                ctx.pipeline_id())

            hex_data = bytes.fromhex(key)

            if len(hex_data) == 0:
                return bytes(), errors.new_common_edgex(
                    errors.ErrKind.CONTRACT_INVALID,
                    f"AES256 encryption key not set in pipeline '{ctx.pipeline_id()}'")

            if len(hex_data) != 64:
                return bytes(), errors.new_common_edgex(
                    errors.ErrKind.CONTRACT_INVALID,
                    f"AES256 encryption key length should be 64 in pipeline '{ctx.pipeline_id()}'")

            return hex_data, None

        return bytes(), errors.new_common_edgex(
            errors.ErrKind.CONTRACT_INVALID, "no key configured")
