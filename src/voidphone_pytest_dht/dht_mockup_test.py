#!/usr/bin/python3

import argparse
import asyncio
import hexdump
import socket
import struct

from util import bad_packet, read_message, handle_client

DHT_ADDR = "127.0.0.1"
DHT_PORT = 7401

DHT_PUT = 650
DHT_GET = 651
DHT_SUCCESS = 652
DHT_FAILURE = 653

storage = {}
storage_lock = None

async def get_from_storage(key):
    global storage, storage_lock
    async with storage_lock:
        try:
            val = storage[key]
            return val
        except KeyError:
            return None

async def save_to_storage(key, val):
    global storage, storage_lock
    async with storage_lock:
        storage[key] = val

async def send_dht_success(reader, writer, key, val):
    raddr, rport = writer.get_extra_info('socket').getpeername()
    msize = int(4 + (256/8) + len(val))
    buf = struct.pack(">HH", msize, DHT_SUCCESS)
    buf += key
    buf += val

    try:
        writer.write(buf)
        await writer.drain()
    except Exception as e:
        print(f"[-] Failed to send DHT_SUCCESS: {e}")
        await bad_packet(reader, writer)
        return False

    print(f"[+] {raddr}:{rport} <<< DHT_SUCCESS: ({key}:{val})")

    return True

async def send_dht_failure(reader, writer, key):
    raddr, rport = writer.get_extra_info('socket').getpeername()
    msize = 4 + (256/8)
    buf = struct.pack(">HH", int(msize), DHT_FAILURE)
    buf += key

    try:
        writer.write(buf)
        await writer.drain()
    except Exception as e:
        print(f"[-] Failed to send DHT_FAILURE: {e}")
        await bad_packet(reader, writer)
        return False

    print(f"[+] {raddr}:{rport} <<< DHT_FAILURE: ({key})")

    return True

async def handle_dht_put(buf, reader, writer):
    raddr, rport = writer.get_extra_info('socket').getpeername()
    header = buf[:4]
    body = buf[4:]

    msize = struct.unpack(">HH", header)[0]
    ttl, rep, res = struct.unpack(">HBB", buf[4:8])

    if msize <= 8 + (256/8) or len(buf) <= 8 + (256/8):
        await bad_packet(reader, writer,
                         f"DHT_PUT with empty value received",
                         buf)
        return False

    key = buf[8: int((256/8)+8)]
    val = buf[int(8 + (256/8)):]

    print(f"[+] {raddr}:{rport} >>> DHT_PUT: ({key}:{val})")

    await save_to_storage(key, val)
    return True

async def handle_dht_get(buf, reader, writer):
    raddr, rport = writer.get_extra_info('socket').getpeername()
    header = buf[:4]
    body = buf[4:]
    msize = struct.unpack(">HH", header)[0]

    if msize != (4 + (256/8)):
        await bad_packet(reader, writer,
                         f"DHT_GET with incorrect size received",
                         buf)
        return False

    key = buf[4:]
    print(f"[+] {raddr}:{rport} >>> DHT_GET: ({key})")

    val = await get_from_storage(key)

    if val:
        ret = await send_dht_success(reader, writer, key, val)
    else:
        ret = await send_dht_failure(reader, writer, key)

    return ret

async def handle_message(buf, reader, writer):
    ret = False
    header = buf[:4]
    body = buf[4:]

    mtype = struct.unpack(">HH", header)[1]
    if mtype == DHT_PUT:
        ret = await handle_dht_put(buf, reader, writer)
    elif mtype == DHT_GET:
        ret = await handle_dht_get(buf, reader, writer)
    else:
        await bad_packet(reader, writer,
                         f"Unknown message type {mtype} received",
                         header)

    return ret

def main():
    host = DHT_ADDR
    port = DHT_PORT

    # parse commandline arguments
    usage_string = ("Run a DHT module mockup with local storage.\n\n"
                   + "Multiple API clients can connect to this same instance.")
    cmd = argparse.ArgumentParser(description=usage_string)
    cmd.add_argument("-a", "--address",
                     help="Bind server to this address")
    cmd.add_argument("-p", "--port",
                     help="Bind server to this port")
    args = cmd.parse_args()

    if args.address is not None:
        host = args.address

    if args.port is not None:
        port = args.port

    # setup storage lock
    global storage_lock
    storage_lock = asyncio.Lock()

    # create asyncio server to listen for incoming API messages
    loop = asyncio.get_event_loop()
    handler = lambda r, w, mhandler=handle_message: handle_client(r,
                                                                  w,
                                                                  mhandler)
    serv = asyncio.start_server(handler,
                                host=host, port=port,
                                family=socket.AddressFamily.AF_INET,
                                reuse_address=True,
                                reuse_port=True)
    loop.create_task(serv)
    print(f"[+] DHT mockup listening on {host}:{port}")

    try:
        loop.run_forever()
    except KeyboardInterrupt as e:
        print("[i] Received SIGINT, shutting down...")
        loop.stop()

if __name__ == '__main__':
    main()
