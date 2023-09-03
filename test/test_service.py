import pytest
import socket
import struct
from src.message_codes import MessageCodes

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))


@pytest.fixture
def setup_socket():
    s = socket.socket(socket.AF_INET, type=socket.SOCK_STREAM)
    s.connect(('127.0.0.1', 7501))
    yield s
    s.close()


def send_get_request(key):
    s = socket.socket(socket.AF_INET, type=socket.SOCK_STREAM)
    s.connect(('127.0.0.1', 7501))
    getreq = struct.pack(">HH32s", int((32 + 256) / 8), MessageCodes.DHT_GET.value, key)
    s.send(getreq)
    buf = s.recv(4096)
    s.close()
    return buf


def send_put_request(socket, key, value):
    putreq = struct.pack(">HHHBB",
                         (4 + 4 + int(256 / 8) + len(value)),
                         MessageCodes.DHT_PUT.value,
                         15,
                         1,
                         0)
    putreq += key
    putreq += value
    socket.send(putreq)


def test_get_non_existing_key(setup_socket):
    s = setup_socket
    key = b'emincanemincanemincanemincanemib'

    buf = send_get_request(key)
    asize, atype = struct.unpack(">HH", buf[:4])
    print(buf)
    print(atype)
    assert atype == MessageCodes.DHT_FAILURE.value


def test_get_existing_key(setup_socket):
    s = setup_socket
    key = b'emincanemincanemincanemincanemib'
    value = b'bernd'

    send_put_request(s, key, value)

    buf = send_get_request(key)
    asize, atype = struct.unpack(">HH", buf[:4])

    print(buf)
    print(atype)

    assert atype == MessageCodes.DHT_SUCCESS.value
