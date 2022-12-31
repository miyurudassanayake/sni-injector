import time, select, threading, time, select, configparser, ssl, os, certifi, socket, warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

class Tunnel():
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read_file(open('settings.ini'))
        self.local_ip = self.config['settings']['local_ip']
        self.listen_port = int(self.config['settings']['listen_port'])

    def tunneling(self, client, stunnel_socket):
        connected = True
        print("[*] Connection Established.")
        while connected == True:
            r, w, x = select.select([client, stunnel_socket], [], [client, stunnel_socket], 3)
            if x:
                connected = False
                break
            for i in r:
                try:
                    data = i.recv(16384)
                    if not data:
                        connected = False
                    if i is stunnel_socket:
                        client.send(data)
                    else:
                        stunnel_socket.send(data)
                except KeyboardInterrupt:
                    print("Exited")
                    connected = False
                except Exception as e:
                    self.logs(f' {e}')
                    connected = False
        client.close()
        stunnel_socket.close()
        self.logs('[*] Client disconnected')
        print("[*] Client disconnected!")

    def destination(self, client, address):
        print("[*] New Client connected!")
        self.logs(f'[*] Client{address}received!')
        try:
            request = client.recv(9124).decode()
            host = self.config['ssh']['host']
            port = request.split(':')[-1].split()[0]
            stunnel_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            stunnel_socket.connect((host, int(port)))
            print(f'[TCP] connected to {host}:{port}')
            self.logs(f'[TCP] connected to {host}:{port}')
            SNI_HOST = self.config['sni']['server_name']
            context = ssl.SSLContext(ssl.PROTOCOL_TLS)
            stunnel_socket = context.wrap_socket(stunnel_socket, server_hostname=str(SNI_HOST))
            context.verify_mode = ssl.CERT_REQUIRED
            context.load_verify_locations(cafile=os.path.relpath(certifi.where()),capath=None, cadata=None)
            self.logs(f'[TCP] Handshaked successfully to {SNI_HOST}')
            print(f'[TCP] Handshaked successfully to {SNI_HOST}')
            self.logs(f"[TCP] Protocol :{stunnel_socket.version()}")
            try:
                self.logs(f"Ciphersuite : {stunnel_socket.cipher()[0]}")
                print(f"[*] Ciphersuite : {stunnel_socket.cipher()[0]}")
            except:pass
            self.logs(f"Peerprincipal: C={stunnel_socket.getpeercert()}")              
            client.send(b"HTTP/1.1 200 Connection Established\r\n\r\n")
            self.tunneling(client, stunnel_socket)
        except Exception as e:
            self.logs(f"[!!!] {e}")
            print(f"[Error] {e}")

    def create_connection(self):
        for res in socket.getaddrinfo(self.local_ip, self.listen_port, socket.AF_UNSPEC, socket.SOCK_STREAM, 0, socket.AI_PASSIVE):
            af, socktype, proto, canonname, sa = res
            try:
                listen_socket = socket.socket(af, socktype, proto)
            except OSError as e:
                self.logs(f"[!!!] {e}")
                print(f"[Error] {e}")
                exit(1)
            try:
                listen_socket.bind((self.local_ip, self.listen_port))
                listen_socket.listen(1)
            except OSError as e:
                self.logs(f"[!!!] {e}")
                print(f"[Error] {e}")
                listen_socket.close()
                exit(1)
                
            self.logs(f'Waiting for incoming connection to : {self.local_ip}:{self.listen_port}\n')
            print(f'Waiting for incoming connection to : {self.local_ip}:{self.listen_port}\n')
            while 1==1:
                try:
                    client, address = listen_socket.accept()
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