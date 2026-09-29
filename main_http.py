#!/usr/bin/env python3
"""
HTTP Custom Payload Injector
Improved version with proper SSH banner waiting
"""

import socket
import select
import threading
import configparser
import time
import os
import sys
import re


class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    ORANGE = "\033[33m"
    RESET = "\033[0m"


class HTTPInjector:
    def __init__(self, config_file="settings.ini"):
        self.config = configparser.ConfigParser()
        if not os.path.exists(config_file):
            print(f"{Colors.RED}[!] {config_file} not found{Colors.RESET}")
            sys.exit(1)

        self.config.read(config_file)

        self.local_ip = self.config.get("settings", "local_ip", fallback="127.0.0.1")
        self.listen_port = self.config.getint("settings", "listen_port", fallback=9092)

        self.ssh_host = self.config.get("ssh", "host", fallback="127.0.0.1")
        self.ssh_port = self.config.getint("ssh", "port", fallback=22)
        self.ssh_user = self.config.get("ssh", "user", fallback="root")

        try:
            self.payload_template = self.config.get("payload", "payload")
        except Exception:
            if self.config.has_section("payload"):
                items = self.config.items("payload")
                if items:
                    self.payload_template = items[0][1]
                else:
                    raise ValueError("No payload found in [payload] section")
            else:
                raise ValueError("Missing [payload] section")

        self.use_proxy = self.config.getboolean("proxy", "enabled", fallback=False)
        if self.use_proxy:
            self.proxy_host = self.config.get("proxy", "host", fallback="")
            self.proxy_port = self.config.getint("proxy", "port", fallback=8080)
        else:
            self.proxy_host = self.ssh_host
            self.proxy_port = self.ssh_port

        self.active_connections = 0
        self.lock = threading.Lock()

        print(f"{Colors.CYAN}[*] HTTP Payload Injector started{Colors.RESET}")
        print(f"    Local       : {self.local_ip}:{self.listen_port}")
        print(f"    SSH Target  : {self.ssh_user}@{self.ssh_host}:{self.ssh_port}")
        if self.use_proxy:
            print(f"    Remote Proxy: {self.proxy_host}:{self.proxy_port}")
        else:
            print(f"    Mode        : Direct")
        print(f"    Payload     : {self.payload_template[:70]}...")
        print("-" * 55)

    def log(self, msg, level="info"):
        timestamp = time.strftime("%H:%M:%S")
        color = {
            "info": Colors.CYAN,
            "success": Colors.GREEN,
            "error": Colors.RED,
            "warn": Colors.YELLOW,
            "payload": Colors.ORANGE,
        }.get(level, Colors.RESET)

        print(f"{color}[{timestamp}] {msg}{Colors.RESET}")

        with open("logs_http.txt", "a") as f:
            f.write(f"[{timestamp}] {msg}\n")

    def format_payload(self, host, port):
        payload = self.payload_template.strip()

        replacements = {
            "[crlf]": "\r\n",
            "[crlf*2]": "\r\n\r\n",
            "[cr]": "\r",
            "[lf]": "\n",
            "[lfcr]": "\n\r",
            "[host]": host,
            "[port]": str(port),
            "[host_port]": f"{host}:{port}",
            "[ssh]": f"{host}:{port}",
            "[protocol]": "HTTP/1.1",
            "[method]": "CONNECT",
            "[ua]": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36",
            "[netData]": f"CONNECT {host}:{port} HTTP/1.1",
            "[raw]": f"CONNECT {host}:{port} HTTP/1.1\r\n\r\n",
            "[real_raw]": f"CONNECT {host}:{port} HTTP/1.1\r\n\r\n",
        }

        for key, value in replacements.items():
            payload = payload.replace(key, value)

        while "  " in payload:
            payload = payload.replace("  ", " ")

        return payload

    def send_payload(self, sock, payload):
        if any(x in payload for x in ["[split]", "[delay_split]", "[instant_split]"]):
            payload = payload.replace("[split]", "||1.0||")
            payload = payload.replace("[delay_split]", "||1.5||")
            payload = payload.replace("[instant_split]", "||0.0||")

            parts = payload.split("||")
            for part in parts:
                if part in ("1.0", "1.5", "0.0"):
                    time.sleep(float(part))
                elif part:
                    sock.sendall(part.encode())
                    self.log(f"Sent split part ({len(part)} bytes)", "payload")
        else:
            sock.sendall(payload.encode())
            self.log(f"Payload sent ({len(payload)} bytes)", "payload")

    def wait_for_ssh_banner(self, remote, client):
        remote.settimeout(12)

        while True:
            try:
                data = remote.recv(4096)
                if not data:
                    self.log("Remote closed while waiting for SSH banner", "error")
                    return False

                text = data.decode("utf-8", errors="ignore")
                first_line = text.split("\n")[0].strip()

                if first_line.startswith("SSH-"):
                    self.log(f"SSH banner received -> {first_line}", "success")
                    client.sendall(data)
                    return True

                if re.match(r"HTTP/\d", first_line):
                    self.log(f"HTTP response: {first_line}", "info")
                    client.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")
                    continue

                self.log(f"Unexpected data: {first_line[:80]}", "warn")
                client.sendall(data)
                return True

            except socket.timeout:
                self.log("Timeout waiting for SSH banner", "error")
                return False
            except Exception as e:
                self.log(f"Error while waiting for banner: {e}", "error")
                return False

    def tunnel(self, client_sock, remote_sock):
        try:
            while True:
                r, _, x = select.select(
                    [client_sock, remote_sock], [], [client_sock, remote_sock], 60
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
                        if sock is client_sock:
                            remote_sock.sendall(data)
                        else:
                            client_sock.sendall(data)
                    except (ConnectionResetError, BrokenPipeError, OSError):
                        return
        finally:
            try:
                client_sock.close()
            except Exception:
                pass
            try:
                remote_sock.close()
            except Exception:
                pass

            with self.lock:
                self.active_connections -= 1
            self.log(f"Connection closed | Active: {self.active_connections}", "warn")

    def handle_client(self, client_sock, address):
        with self.lock:
            self.active_connections += 1

        self.log(f"New client {address[0]}:{address[1]} | Active: {self.active_connections}")

        try:
            request = client_sock.recv(4096).decode(errors="ignore")
            if not request:
                client_sock.close()
                return

            target_host = self.ssh_host
            target_port = str(self.ssh_port)

            payload = self.format_payload(target_host, target_port)

            remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            remote.settimeout(15)
            remote.connect((self.proxy_host, int(self.proxy_port)))
            self.log(f"TCP connected -> {self.proxy_host}:{self.proxy_port}")

            self.send_payload(remote, payload)

            if not self.wait_for_ssh_banner(remote, client_sock):
                remote.close()
                client_sock.close()
                return

            remote.settimeout(None)
            client_sock.settimeout(None)

            self.log("Tunnel established - starting relay", "success")
            self.tunnel(client_sock, remote)

        except socket.timeout:
            self.log("Connection timed out", "error")
            try:
                client_sock.close()
            except Exception:
                pass
        except Exception as e:
            self.log(f"Error: {e}", "error")
            try:
                client_sock.close()
            except Exception:
                pass
        finally:
            with self.lock:
                if self.active_connections > 0:
                    self.active_connections -= 1

    def start(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            server.bind((self.local_ip, self.listen_port))
            server.listen(50)
            self.log(f"Listening on {self.local_ip}:{self.listen_port}", "success")
        except OSError as e:
            self.log(f"Cannot bind: {e}", "error")
            sys.exit(1)

        print(f"\n{Colors.YELLOW}Run this SSH command in another terminal:{Colors.RESET}")
        print(f'ssh -C -o "ProxyCommand=nc -X CONNECT -x {self.local_ip}:{self.listen_port} %h %p" \\')
        print(f'    {self.ssh_user}@{self.ssh_host} -p {self.ssh_port} -CND 1080 \\')
        print(f'    -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null\n')
        print(f"{Colors.CYAN}After login, set your apps to SOCKS5 -> 127.0.0.1:1080{Colors.RESET}\n")

        try:
            while True:
                client, addr = server.accept()
                t = threading.Thread(
                    target=self.handle_client, args=(client, addr), daemon=True
                )
                t.start()
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}[*] Shutting down...{Colors.RESET}")
            if os.path.exists("logs_http.txt"):
                os.remove("logs_http.txt")
        finally:
            server.close()


if __name__ == "__main__":
    injector = HTTPInjector()
    injector.start()