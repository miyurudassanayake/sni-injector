import time, select, threading, time, select, configparser, ssl, os, certifi, socket, warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

class Tunnel():
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read_file(open('settings.ini'))
        self.local_ip = self.config['settings']['local_ip']
        self.listen_port = int(self.config['settings']['listen_port'])

    def tunneling(self, client, sockt):
        connected = True
        print("[*] Connection Established.")
        while connected == True:
            r, w, x = select.select([client, sockt], [], [client, sockt], 3)
            if x:
                connected = False
                break
            for i in r:
                try:
                    data = i.recv(16384)
                    if not data:
                        connected = False
                    if i is sockt:
                        client.send(data)
                    else:
                        sockt.send(data)
                except KeyboardInterrupt:
                    print("Exited")
                    connected = False
                except Exception as e:
                    self.logs(f' {e}')
                    connected = False
        client.close()
        sockt.close()
        self.logs('[*] Client disconnected')
        print("[*] Client disconnected!")

    def destination(self, client, address):
        print("[*] New Client connected!")
        try:
            self.logs(f'[*] Client{address}received!')
            request = client.recv(9124).decode()
            host = self.config['ssh']['host']
            port = request.split(':')[-1].split()[0]
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((host, int(port)))
            self.logs(f'[TCP] connected to {host}:{port}')
            print(f'[TCP] connected to {host}:{port}')
            
            SNI_HOST = self.config['sni']['server_name']
            context = ssl.SSLContext(ssl.PROTOCOL_TLS)
            s = context.wrap_socket(s, server_hostname=str(SNI_HOST))
            context.verify_mode = ssl.CERT_REQUIRED
            context.load_verify_locations(cafile=os.path.relpath(certifi.where()),capath=None, cadata=None)
            self.logs(f'[TCP] Handshaked successfully to {SNI_HOST}')
            print(f'[TCP] Handshaked successfully to {SNI_HOST}')
            self.logs(f"[TCP] Protocol :{s.version()}")
            try:
                self.logs(f"Ciphersuite : {s.cipher()[0]}")
                print(f"[*] Ciphersuite : {s.cipher()[0]}")
            except:pass
            self.logs(f"Peerprincipal: C={s.getpeercert()}")              
            client.send(b"HTTP/1.1 200 Connection Established\r\n\r\n")
            self.tunneling(client, s)
        except Exception as e:
            self.logs(f"[!!!] {e}")
            print(f"[Error] {e}")

    def create_connection(self):
        for res in socket.getaddrinfo(self.local_ip, self.listen_port, socket.AF_UNSPEC, socket.SOCK_STREAM, 0, socket.AI_PASSIVE):
            af, socktype, proto, canonname, sa = res
            try:
                sockt = socket.socket(af, socktype, proto)
            except OSError as e:
                self.logs(f"[!!!] {e}")
                print(f"[Error] {e}")
                exit()
            try:
                localAddress = socket.gethostbyname("localhost")
                sockt.bind((localAddress, self.listen_port))
                sockt.listen(1)
            except OSError as e:
                self.logs(f"[!!!] {e}")
                print(f"[Error] {e}")
                sockt.close()
                exit()
                
            self.logs('Waiting for incoming connection to : {}:{}\n'.format(self.local_ip, self.listen_port))
            print(f'Waiting for incoming connection to : {self.local_ip}:{self.listen_port}\n')
            while True:
                try:
                    client, address = sockt.accept()
                    thread = threading.Thread(target=self.destination, args=(client, address)).start()
                except KeyboardInterrupt:
                    print("\n[*] Exiting...")  
                    if os.path.exists("logs.txt"):os.remove("logs.txt")
                    break

    def logs(self, log):
        logtime = str(time.ctime()).split()[3]
        logfile = open('logs.txt', 'a')
        logfile.write(f'[{logtime}] : {str(log)}\n')


if __name__ == '__main__':
    start = Tunnel()
    start.create_connection()
