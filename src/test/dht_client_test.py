#!/usr/bin/python3

import argparse
import hexdump
import socket
import struct
import time

target_ip = '127.0.0.1'
target_port = 7401

dht_key = b'emincanemincanemincanemincanemin'
dht_value = b'bernd'

DHT_PUT = 650
DHT_GET = 651
DHT_SUCCESS = 652
DHT_FAILURE = 653

HOST_DISCONNECTS = False


def send_get(s, dht_key):
    getreq = struct.pack(">HH32s", int((32 + 256) / 8), DHT_GET, dht_key)
    print("[+] Sending GET request...")
    try:
        s.send(getreq)
    except Exception as e:
        print(f"[-] Sending of packet failed: {e}.")
        return False

    buf = s.recv(4096)
    if buf == b'':
        print('[-] Connection closed by other endpoint.')
        return False

    try:
        asize, atype = struct.unpack(">HH", buf[:4])
        akey = buf[4:int(256 / 8) + 4]

        if atype == DHT_SUCCESS:
            avalue = buf[int(256 / 8) + 4:]
            print(f"[+] Received DHT_SUCCESS."
                  + f" size: {asize}, key: {akey}, value: {avalue}")
        elif atype == DHT_FAILURE:
            print(f"[+] Received DHT_FAILURE."
                  + f" size: {asize}, key: {akey}")
        else:
            print("[-] Received unexpected answer")
            hexdump.hexdump(buf)
    except Exception as e:
        print(f"[-] Parsing of packet failed: {e}.")
        hexdump.hexdump(buf)

    return True


def send_put(s, dht_key, dht_value):
    putreq = struct.pack(">HHHBB",
                         (4 + 4 + int(256 / 8) + len(dht_value)),
                         DHT_PUT,
                         1,
                         1,
                         0)
    putreq += dht_key
    putreq += dht_value

    print("[+] Sending PUT request...")

    try:
        s.send(putreq)
    except Exception as e:
        print(f"[-] Sending of packet failed: {e}.")
        return False

    return True


def get_socket(host, port):
    print(f"Trying to connect to {host}:{port}")
    s = socket.socket(socket.AF_INET, type=socket.SOCK_STREAM)
    s.connect((host, port))
    return s


def main():
    host = target_ip
    port = target_port
    key = dht_key
    value = dht_value

    # parse commandline arguments
    usage_string = ("Run a DHT client mockup.\n\n")
    cmd = argparse.ArgumentParser(description=usage_string)
    cmd.add_argument("-a", "--address",
                     help="Server address to connect to")
    cmd.add_argument("-p", "--port",
                     help="Server port to connect to")
    cmd.add_argument("-s", "--set", action="store_true",
                     help="Send DHT_PUT to the server")
    cmd.add_argument("-g", "--get", action="store_true",
                     help="Send DHT_GET to the server")
    cmd.add_argument("-k", "--key",
                     help="Optionally use this key in requests")
    cmd.add_argument("-d", "--data",
                     help="Optionally use this data in requests")
    cmd.add_argument("-c", "--cont", action="store_true",
                     help="Optionally continue sending requests")
    args = cmd.parse_args()

    if args.address is not None:
        host = args.address

    if args.port is not None:
        port = int(args.port)

    if args.key is not None:
        key = bytes(args.key, encoding='utf-8')
        if len(key) != 32:
            key += bytes(32 - len(key))

    if args.data is not None:
        if len(args.data) >= 1:
            value = bytes(args.data, encoding='utf=8')

    s = get_socket(host, port)
    print(f"[+] Connected to {host}:{port}")

    print(args)

    while True:
        success = False

        if args.set:
            success = send_put(s, key, value)
            time.sleep(0.5)

            if HOST_DISCONNECTS or not success:
                s.close()
                s = get_socket(host, port)
                success = True
                print(f"[+] Connected to {host}:{port}")

        if args.get:
            success = send_get(s, key)

        if args.cont is False:
            break

        input("Press enter to send next request iteration")

        if HOST_DISCONNECTS or not success:
            s.close()
            s = get_socket(host, port)
            success = True
            print(f"[+] Connected to {host}:{port}")

    s.close()


if __name__ == '__main__':
    main()
