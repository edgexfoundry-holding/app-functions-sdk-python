#  Copyright (C) 2024 IOTech Ltd
#  SPDX-License-Identifier: Apache-2.0
"""
This module provides the classes and functions for Sqlite store client
"""
import base64
import copy
import json
import sqlite3
import threading
import time
from typing import Optional, Tuple

from ....contracts import errors
from ....contracts.clients.logger import Logger
from ....contracts.clients.utils.common import convert_any_to_dict
from ....contracts.dtos.store_object import StoredObject
from ....interfaces.store import StoreClient


class Client(StoreClient):
    """ Sqlite store client """

    def retrieve_from_store(
            self, app_service_key: str) -> Tuple[list[StoredObject], Optional[errors.EdgeX]]:
        if app_service_key == "":
            return [], errors.new_common_edgex(
                errors.ErrKind.CONTRACT_INVALID, "no AppServiceKey provided")
        with self.conn_mutex:
            with self.conn:
                try:
                    cur = self.conn.execute(
                        "SELECT content FROM store WHERE app_service_key = $1", [app_service_key])
                    objects: list[sqlite3.Row] = cur.fetchall()
                except sqlite3.Error as e:
                    return [], errors.new_common_edgex_wrapper(e)
                res = []
                for row in objects:
                    payload_dict = json.loads(row['content'])
                    obj = StoredObject(**payload_dict)
                    if is_base64(obj.payload):
                        # convert base64 back to bytes
                        obj.payload = base64.b64decode(obj.payload)
                    res.append(obj)
                return res, None

    def update(self, o: StoredObject) -> Optional[errors.EdgeX]:
        err = o.validate_contract(True)
        if err is not None:
            return errors.new_common_edgex_wrapper(err)

        with self.conn_mutex:
            with self.conn:
                try:
                    data = copy.deepcopy(o)
                    cur = self.conn.execute("SELECT id FROM store WHERE id = $1", [data.id])
                    res = cur.fetchone()
                    if res is None:
                        self.lc.info("stored object %s not exists, can not update", data.id)
                        return errors.new_common_edgex(
                            errors.ErrKind.ENTITY_DOES_NOT_EXIST,
                            f"stored object {data.id} not exists, can not update")

                    if isinstance(o.payload, bytes):
                        # encode to base64 string for JSON serialize
                        data.payload = base64.b64encode(data.payload).decode()
                    json_data = json.dumps(convert_any_to_dict(data))
                    self.conn.execute(
                        "UPDATE store SET content = ? WHERE id = ?",
                        (json_data, data.id))
                    return None
                except sqlite3.Error as e:
                    return errors.new_common_edgex_wrapper(e)

    def remove_from_store(self, o: StoredObject) -> Optional[errors.EdgeX]:
        err = o.validate_contract(True)
        if err is not None:
            return errors.new_common_edgex_wrapper(err)
        with self.conn_mutex:
            with self.conn:
                try:
                    self.conn.execute("DELETE FROM store WHERE id = ?", [o.id])
                except sqlite3.Error as e:
                    return errors.new_common_edgex_wrapper(e)
        return None

    def disconnect(self) -> Optional[errors.EdgeX]:
        return self.conn.close()

    def __init__(self, conn: sqlite3.Connection, lc: Logger):
        self.lc = lc
        self.conn = conn
        self.conn.row_factory = sqlite3.Row
        self.conn_mutex = threading.Lock()
        with self.conn_mutex:
            with conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS store (
                        id character PRIMARY KEY,
                        app_service_key character NOT NULL,
                        created int NOT NULL,
                        content text NOT NULL
                    )
                    """)

    def store(self, o: StoredObject) -> Tuple[str, Optional[errors.EdgeX]]:
        """ Store persists a stored object to the store table and returns the assigned UUID """
        err = o.validate_contract(False)
        if err is not None:
            return "", errors.new_common_edgex_wrapper(err)

        data = copy.deepcopy(o)
        if isinstance(data.payload, bytes):
            # encode to base64 string for JSON serialize
            data.payload = base64.b64encode(data.payload).decode()

        with self.conn_mutex:
            with self.conn:
                try:
                    cur = self.conn.execute("SELECT id FROM store WHERE id = $1", [data.id])
                    res = cur.fetchone()
                    if res:
                        self.lc.info("stored object %s already exists, not persist", data.id)
                        return "", None

                    json_data = json.dumps(convert_any_to_dict(data))
                    timestamp = time.time() * 1000
                    self.conn.execute(
                        "INSERT INTO store(id, app_service_key, content, created) "
                        "VALUES ($1, $2, $3, $4)",
                        (data.id, data.appServiceKey, json_data, timestamp))
                    return data.id, None
                except sqlite3.Error as e:
                    return "", errors.new_common_edgex_wrapper(e)


def new_sqlite_client(path: str, lc: Logger) -> StoreClient:
    """ Create a sqlite client """
    try:
        # using thread lock instead of check_same_thread
        conn = sqlite3.connect(path, check_same_thread=False)
    except Exception as e:
        raise e
    return Client(conn, lc)


def is_base64(s):
    """ Checker whether the string is valid base64 format """
    try:
        return base64.b64encode(base64.b64decode(s)).decode() == s
    except Exception:  # pylint: disable=broad-exception-caught
        return False
