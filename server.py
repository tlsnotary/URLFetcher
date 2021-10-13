import socket, json, time, hashlib, subprocess, threading, os
arPath = 'app/attestation_retriever' #attestation retriever app's path
erPath = 'app/entropy_retriever' #entropy retriever app's path

def haveged():
    # Keep haveged running in the foreground
    print("starting haveged")
    subprocess.run(['haveged','-F','-v','1'])

def rngd():
    # Keep rngd running in the foreground
    print("starting rngd")
    subprocess.run(['rngd','-f','-r','/tmp/rnd'])

if __name__ == "__main__":
    threading.Thread(target=haveged).start()
    nsm_random = b''
    i = 0
    while len(nsm_random) < 10000:
        out = subprocess.check_output([erPath])
        nsm_random += bytes(json.loads(out.decode()))
        i+=1
        if i > 1000:
            raise('Could not get 10000 random bytes from NSM')
    print("got entropy bytes from NSM:", len(nsm_random))
    with open('/tmp/rnd', 'wb+') as f:
        f.write(nsm_random)
    threading.Thread(target=rngd).start()
    # allow haveged to populate
    time.sleep(5)
    # check 1
    with open("/proc/sys/kernel/random/entropy_avail", 'r') as f:
        data = f.read()
        entropy = int(data.strip())
        print("/proc/sys/kernel/random/entropy_avail is ", entropy)
        if entropy < 2000:
            raise Exception("not enough entropy in /proc/sys/kernel/random/entropy_avail")
    # check 2. Returns non-0 if randomness is bad
    rv = os.system("cat /dev/random | rngtest -c 100")
    if rv != 0:
        raise Exception("rngtest failed")
    print("rngtest passed")

    print("server is listening")
    sock = socket.socket(socket.AF_VSOCK, socket.SOCK_STREAM)
    sock.bind((socket.VMADDR_CID_ANY, 10011))
    sock.listen(1)
    connection, client_address = sock.accept()
    connection.settimeout(2)
    try:
        raw = connection.recv(10000)
        # usually the body arrives separately from the headers, so give the TCP buffer some time to fill up
        time.sleep(1)
        raw += connection.recv(10000)
    except:
        # socket timeout
        pass
    print('received', raw)
    # ignore HTTP headers, we just need the payload in the body
    body = raw.decode().split('\r\n\r\n')[1]
    json_object = json.loads(body)
    final_json = []
    for url in json_object:
        contents = subprocess.check_output(["curl", "-x", "127.0.0.1:8001", url])       
        final_json.append({"request":url, "response":contents.decode()})
    print(final_json)
    data_to_be_hashed = json.dumps(final_json).encode()
    digest_for_attestation = hashlib.sha256(data_to_be_hashed).digest()
    with open('/tmp/digest', 'wb+') as f:
        f.write(digest_for_attestation)
    subprocess.call([arPath, '/tmp/digest', '/tmp/attest'])
    with open('/tmp/attest', 'rb') as f:
        attestDoc = f.read()
    connection.send(len(data_to_be_hashed).to_bytes(4, 'big') + data_to_be_hashed + attestDoc)
    connection.close()
