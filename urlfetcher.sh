#!/bin/bash

#this is the main entrypoint of the urlfetcher container

ifconfig lo 127.0.0.1

# traffic-forwarder.py takes data from enclave's vsock at port 8001
# and forwards it to host's vsock 8002
# where vsock-proxy takes data from host's vsock 8002 and
# forwards it to host's TCP port e.g. 8888 where the a socks proxy server
# should be listening
# (on host machine we run vsock-proxy 8002 127.0.0.1 8888 --config config.yaml)

python3 /app/traffic-forwarder.py 8001 3 8002 &
python3 /app/server.py