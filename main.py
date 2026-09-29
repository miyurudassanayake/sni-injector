#!/usr/bin/env python3
"""
SNI/SSL Tunnel
Improved version: threaded, thread-safe connection tracking,
proper logging, cleaner error handling, graceful shutdown.
"""

import time
import select
import threading
import configparser
import ssl
import os
import sys
import socket
import warnings

import certifi

warnings.filterwarnings("ignore", category=DeprecationWarning)


class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    ORANGE = "\033[33m"
    RESET = "\033[0m"


class Tunnel:
    def __init__(self, config_file="settings.ini"):
        self.config = configparser.ConfigParser()
        if not os.path.exists(config_file):
            print(f"{Colors.RED}[!] {config_file} not found{Colors.RESET}")
            sys.exit(1)

        self.config.read(config_file)

        self.local_ip = self.config.get("settings", "local_ip", fallback="127.0.0.1")
        self.listen_port = self.config.getint("settings", "listen_port", fallback=8080)

        self.ssh_host = self.config.get("ssh", "host", fallback="127.0.0.1")
        self.ssh_port = self.config.getint("ssh", "port", fallback=443)

        self.sni_host = self.config.get("sni", "server_name", fallback=self.ssh_host)

        self.active_connections = 0
        self.lock = threading.Lock()

        print(f"{Colors.CYAN}[*] SNI/SSL Tunnel started{Colors.RESET}")
        print(f"    Local     : {self.local_ip}:{self.listen_port}")
        print(f"    Target    : {self.ssh_host}:{self.ssh_port}")
        print(f"    SNI       : {self.sni_host}")
        print("-" * 55)

    def log(self, msg, level="info"):
        timestamp = time.strftime("%H:%M:%S")
        color = {
            "info": Colors.CYAN,
            "success": Colors.GREEN,
            "error": Colors.RED,
            "warn": Colors.YELLOW,
        }.get(level, Colors.RESET)
        print(f"{color}[{timestamp}] {msg}{Colors.RESET}")
        try:
            with open("logs.txt", "a") as f:
                f.write(f"[{timestamp}] {msg}\n")
        except OSError:
            pass

    def tunneling(self, client, remote_socket):
        try:
            while True:
                r, _, x = select.select(
                    [client, remote_socket], [], [client, remote_socket], 60
                )
                if x:
                    break
                if not r:
                    continue
                for sock in r:
                    try:
                        data = sock.recv(32768)
                        if not data:
                            return
                        if sock is remote_socket:
                            client.sendall(data)
                        else:
                            remote_socket.sendall(data)
                    except (ConnectionResetError, BrokenPipeError, OSError):
                        return
        finally:
            for s in (client, remote_socket):
                try:
                    s.close()
                except Exception:
                    pass
            with self.lock:
                self.active_connections -= 1
            self.log(f"Connection closed | Active: {self.active_connections}", "warn")

    def destination(self, client, address):
        with self.lock:
            self.active_connections += 1
        self.log(f"New client {address[0]}:{address[1]} | Active: {self.active_connections}")

        remote_socket = None
        closed_by_helper = False
        try:
            client.settimeout(15)
            request = client.recv(9124).decode(errors="ignore")
            if not request:
                self.log("Empty request from client", "warn")
                client.close()
                with self.lock:
                    self.active_connections -= 1
                return

            host = self.ssh_host
            try:
                port = int(request.split(":")[-1].split()[0])
            except (ValueError, IndexError):
                port = self.ssh_port

            remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote_socket.settimeout(15)
            remote_socket.connect((host, port))
            self.log(f"TCP connected -> {host}:{port}")

            context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            context.verify_mode = ssl.CERT_REQUIRED
            context.load_verify_locations(cafile=certifi.where())

            remote_socket = context.wrap_socket(remote_socket, server_hostname=self.sni_host)
            self.log(f"TLS handshake OK -> {self.sni_host}", "success")
            self.log(f"Protocol: {remote_socket.version()}")
            try:
                cipher = remote_socket.cipher()
                if cipher:
                    self.log(f"Cipher: {cipher[0]}")
            except Exception:
                pass

            client.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")
            remote_socket.settimeout(None)
            client.settimeout(None)

            self.log("Tunnel established - starting relay", "success")
            closed_by_helper = True
            self.tunneling(client, remote_socket)  # decrements active_connections itself

        except socket.timeout:
            self.log("Connection timed out", "error")
        except Exception as e:
            self.log(f"Error: {e}", "error")
        finally:
            if not closed_by_helper:
                for s in (client, remote_socket):
                    if s:
                        try:
                            s.close()
                        except Exception:
                            pass
                with self.lock:
                    self.active_connections -= 1

    def create_connection(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            server.bind((self.local_ip, self.listen_port))
            server.listen(50)
            self.log(f"Listening on {self.local_ip}:{self.listen_port}", "success")
        except OSError as e:
            self.log(f"Cannot bind: {e}", "error")
            sys.exit(1)

        try:
            while True:
                client, address = server.accept()
                t = threading.Thread(
                    target=self.destination, args=(client, address), daemon=True
                )
                t.start()
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}[*] Shutting down...{Colors.RESET}")
            if os.path.exists("logs.txt"):
                try:
                    os.remove("logs.txt")
                except OSError:
                    pass
        finally:
            server.close()


if __name__ == "__main__":
    tunnel = Tunnel()
    tunnel.create_connection()