import hexdump
import socket
import struct
import sys

def sync_bad_packet(buf, sock, reason="Unknown or malformed data received"):
    print(f"[-] {reason}:")
    hexdump.hexdump(buf)
    print("[-] Exiting.")
    sock.close()
    sys.exit(-1)

def connect_socket(addr, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((addr, port))
    return s

def sync_read_message(s, fail_reason="Server closed the connection"):
    try:
        msizebuf = s.recv(2)
        buflen = struct.unpack(">H", msizebuf)[0]
        buf = msizebuf + s.recv(buflen - 2)
    except Exception as e:
        if msizebuf != b'':
            sync_bad_packet(buf, s, str(e))
        else:
            sync_bad_packet(b'', s, fail_reason)
    return buf

async def bad_packet(reader, writer, reason='', data=b'', cleanup_func=None):
    try:
        raddr, rport = writer.get_extra_info('socket').getpeername()
    except OSError:
        writer.close()
        await writer.wait_closed()
        print(f"[i] (Unknown) xxx Connection closed abruptly, state may remain")
        return

    if reason != '':
        print(f"[-] {raddr}:{rport} >>> {reason}:\n")
        hexdump.hexdump(data)
        print('')

    if cleanup_func:
        await cleanup_func((reader,writer))

    writer.close()
    await writer.wait_closed()
    print(f"[i] {raddr}:{rport} xxx Connection closed")

async def read_message(reader, writer, cleanup_func=None):
    if writer.is_closing():
        await bad_packet(reader, writer, cleanup_func=cleanup_func)
        return b''

    try:
        raddr, rport = writer.get_extra_info('socket').getpeername()
    except OSError:
        await bad_packet(reader, writer, cleanup_func=cleanup_func)
        return b''

    try:
        msizebuf = await reader.read(2)
        buflen = struct.unpack(">H", msizebuf)[0]
        buf = msizebuf + await reader.read(buflen)
    except Exception as e:
        if msizebuf != b'':
            await bad_packet(reader, writer,
                             "Malformed data received", msizebuf, cleanup_func)
        else:
            await bad_packet(reader, writer, cleanup_func=cleanup_func)

        buf = b''
    return buf

async def handle_client(reader, writer, handle_message, cleanup_func=None):
    raddr, rport = writer.get_extra_info('socket').getpeername()
    print(f"[+] {raddr}:{rport} >>> Incoming connection")

    while True:
        buf = await read_message(reader, writer, cleanup_func=cleanup_func)
        if buf == b'':
            return

        if not await handle_message(buf, reader, writer):
            return
