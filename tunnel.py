import time, select, threading, time, select, configparser, ssl, os, certifi, socket, re, warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)
Buffer_lenght = 4096 * 4

class injector:
    def __init__(self):
        pass

    def payloadformating(self, payload, host, port):
        self.logs(f'[TCP] Sending payload :\n{payload}')
        payload = payload.replace('[crlf]', '\r\n')
        payload = payload.replace('[crlf*2]', '\r\n\r\n')
        payload = payload.replace('[cr]', '\r')
        payload = payload.replace('[lf]', '\n')
        payload = payload.replace('[protocol]', 'HTTP/1.0')
        payload = payload.replace('[ua]', 'Dalvik/2.1.0')
        payload = payload.replace('[raw]', 'CONNECT '+host+':'+port+' HTTP/1.0\r\n\r\n')
        payload = payload.replace('[real_raw]', 'CONNECT '+host+':'+port+' HTTP/1.0\r\n\r\n')
        payload = payload.replace('[netData]', 'CONNECT '+host+':'+port + ' HTTP/1.0')
        payload = payload.replace('[realData]', 'CONNECT '+host+':'+port+' HTTP/1.0')
        payload = payload.replace('[split_delay]', '[delay_split]')
        payload = payload.replace('[split_instant]', '[instant_split]')
        payload = payload.replace('[method]', 'CONNECT')
        payload = payload.replace('mip', '127.0.0.1')
        payload = payload.replace('[ssh]', host+':'+port)
        payload = payload.replace('[lfcr]', '\n\r')
        payload = payload.replace('[host_port]', host+':'+port)
        payload = payload.replace('[host]', host)
        payload = payload.replace('[port]', port)
        payload = payload.replace('[auth]', '')
        return payload

    def get_resp(self, server, client):
        packet = server.recv(1024)
        res = packet.decode('utf-8', 'ignore')
        status = res.split('\n')[0]
        if status.split('-')[0] == 'SSH':
            self.logs(f'response : {status}')
            client.send(packet)
            return True
        else:
            if re.match(r'HTTP/\d(\.\d)? \d\d\d ', status):
                self.logs(f'response : {status}')
            client.send(b'HTTP/1.1 200 Connection established\r\n\r\n')
            return self.get_resp(server, client)

    def logs(self, log):
        logtime = str(time.ctime()).split()[3]
        logfile = open('logs.txt', 'a')
        logfile.write(f'[{logtime}] : {str(log)}\n')

class Tunnel(injector):
    def __init__(self):
        self.localip = '127.0.0.1'
        self.LISTEN_PORT = 9092

    def conf(self):
        config = configparser.ConfigParser()
        try:
            config.read_file(open('settings.ini'))
        except Exception as e:
            self.logs(e)
        return config

    def extraxt_sni(self, config):
        sni = config['sni']['server_name']
        return sni

    def gethost(self, config):
        host = config['ssh']['host']
        return host

    def tunneling(self, client, sockt):
        connected = True
        print("[*] New Client connected!")
        while connected == True:
            r, w, x = select.select([client, sockt], [], [client, sockt], 3)
            if x:
                connected = False
                break
            for i in r:
                try:
                    data = i.recv(Buffer_lenght)
                    if not data:
                        connected = False
                        break
                    if i is sockt:
                        client.send(data)
                    else:
                        sockt.send(data)
                except KeyboardInterrupt:
                    print("Exited")
                    break
                except Exception as e:
                    self.logs(f' {e}')
                    connected = False
                    break
        client.close()
        sockt.close()
        self.logs('[*] Client disconnected')
        print("[*] Client disconnected!")
        if os.path.exists("logs.txt"):os.remove("logs.txt")

    def destination(self, client, address):
        try:
            self.logs(f'[*] Client{address}received!')
            request = client.recv(9124).decode()
            host = self.gethost(self.conf())
            port = request.split(':')[-1].split()[0]
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((host, int(port)))
            self.logs(f'[TCP] connected to {host}:{port}')
            
            SNI_HOST = self.extraxt_sni(self.conf())
            context = ssl.SSLContext(ssl.PROTOCOL_TLS)
            s = context.wrap_socket(s, server_hostname=str(SNI_HOST))
            context.verify_mode = ssl.CERT_REQUIRED
            context.load_verify_locations(cafile=os.path.relpath(certifi.where()),capath=None, cadata=None)
            self.logs(f'[TCP] Handshaked successfully to {SNI_HOST}')
            self.logs(f"[TCP] Protocol :{s.version()}")
            try:self.logs(f"Ciphersuite : {s.cipher()[0]}")
            except:pass
            self.logs(f"Peerprincipal: C={s.getpeercert()}")              
            client.send(b"HTTP/1.1 200 Connection Established\r\n\r\n")
            self.tunneling(client, s)
        except Exception as e:
            self.logs(f"[!!!] {e}")

    def create_connection(self):
        for res in socket.getaddrinfo(self.localip, self.LISTEN_PORT, socket.AF_UNSPEC, socket.SOCK_STREAM, 0, socket.AI_PASSIVE):
            af, socktype, proto, canonname, sa = res
            try:
                sockt = socket.socket(af, socktype, proto)
            except OSError as e:
                self.logs(f"[!!!] {e}")
                print(f"[Error] {e}")
                exit()
            try:
                localAddress = socket.gethostbyname("localhost")
                sockt.bind((localAddress, self.LISTEN_PORT))
                sockt.listen(1)
            except OSError as e:
                self.logs(f"[!!!] {e}")
                print(f"[Error] {e}")
                sockt.close()
                exit()
                
            self.logs('Waiting for incoming connection to : {}:{}\n'.format(self.localip, self.LISTEN_PORT))
            while True:
                try:
                    client, address = sockt.accept()
                    thread = threading.Thread(target=self.destination, args=(client, address)).start()
                except KeyboardInterrupt:
                    print("\n[*] Exiting...")
                    self.logs("User exit.")
                    exit()

    def logs(self, log):
        logtime = str(time.ctime()).split()[3]
        logfile = open('logs.txt', 'a')
        logfile.write(f'[{logtime}] : {str(log)}\n')


if __name__ == '__main__':
    start = Tunnel()
    start.create_connection()
