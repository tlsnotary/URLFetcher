# tcp_proxy.py does 2 things:
# 1. forwards requests from host's port 10011 to enclave's port 10011
# 2. allows the enclave to make http requests to the outside world by runnning the vsock-proxy utility
# to forward requests from host's vsock port 8002 to host's port 8888 on which
# an http proxy should be listening (e.g. ).
# Inside the enclave traffic-forwarder.py must be run so that traffic from enclave's vsock port 
# could be forwarded to host's vsock port 8002

import socket, time
import subprocess
import threading

def handler(sock):
#only process one request and close the socket
    print('Handling a new connection', sock.fileno())
    raw = None
    try:
        sock.settimeout(20)
        raw = sock.recv(1000000)
        if not raw:
            print('No data received', sock.fileno())
            sock.close()
            return
        #\r\n\r\n separates the headers from the POST payload
        headers = raw.decode().split('\r\n\r\n')[0].split('\r\n')
        expectedPayloadLength = None
        headerFound = False
        for h in headers:
            if h.startswith('Content-Length'):
                expectedPayloadLength = int(h.split(':')[1].strip())
                headerFound = True
                break
        if not headerFound:
            print('Error: Content-Length header not found')
            return
        payload = raw.decode().split('\r\n\r\n')[1]
        payloadLengthIsCorrect = False
        for x in range(10):
            if len(payload) < expectedPayloadLength:
                raw += sock.recv(1000000)
                payload = raw.decode().split('\r\n\r\n')[1]
                time.sleep(0.1)
                print('waiting for more payload')
            else:
                payloadLengthIsCorrect = True
        if not payloadLengthIsCorrect:
            print('Error: payload length is incorrect')
            return
        #forward raw data to the enclave
        client_sock = socket.socket(socket.AF_VSOCK, socket.SOCK_STREAM)
        client_sock.settimeout(60)
        client_sock.connect((16, 10011))
        client_sock.sendall(raw)
        response = client_sock.recv(1000000)
        sock.send(response)
        sock.close()

    except Exception as e: #e.g. base64 decode exception
        print('Exception while handling connection', sock.fileno(), e, raw)
        sock.close()


def vsock():
    subprocess.call(['vsock-proxy', '8002', '127.0.0.1', '8888', '--config', 'vsockconfig.yaml'])


if __name__ == "__main__":
    threading.Thread(target=vsock).start()

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_address = ('0.0.0.0', 10011)
    sock.bind(server_address)

    sock.listen(100) #as many as possible
    connection_number = 0
    while True:
        try:
            print('Waiting for a new connection')
            connection, client_address = sock.accept()
            connection_number += 1
            print('Connection accepted', connection_number)
            threading.Thread(target=handler, args=(connection,)).start()
        except Exception as e:
            print('Exception in notaryserver.py', e)
            pass