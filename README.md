# Python SSH SSL SNI Injector For Free Internet [HTTP Injector]

<p align="center">
   <a href="#installation">Installation & Usage</a>
   &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;
   <a href="#introduction">Introduction</a>
</p>

## Introduction

### What is SNI?

[***Server Name Indication (SNI)***](https://en.wikipedia.org/wiki/Server_Name_Indication) is an extension to the Transport Layer Security (TLS) computer networking protocol by which a client indicates which hostname it is attempting to connect to at the start of the handshaking process.This allows a server to present one of multiple possible certificates on the same IP address and TCP port number and hence allows multiple secure (HTTPS) websites (or any other service over TLS) to be served by the same IP address without requiring all those sites to use the same certificate [<sup>Read more</sup>](https://en.wikipedia.org/wiki/Server_Name_Indication)

Here's a screenshot of **Wireshark** while I'm attempting to connect to zoom.us via https.
<img src="https://github.com/miyurudassanayake/sni-injector/blob/main/static/wireshark.png" width="70%"><br>
As you can see, I applied the <code>ssl.handshake.extensions server name=zoom.us</code> filter to wireshark to filter ssl handshakes where sni is <code>zoom.us</code>.

### What is SNI BUG Host

SNI bug hosts can be in various forms. They can be a packet host, a free CDN host, government portals, zero-rated websites, social media (subscription), and a variety of other sites. They also do a fantastic job of getting over your Internet service provider's firewall.

If you have a subscription to <code>zoom.us</code> and want to visit Zoom, your ISP's firewall will scan every time your SSL handshake to determine if the SNI is "zoom.us", and if it does, the firewall will enable you to keep that connection free fo charge. When you have a subscription to access internet, this is what happens.

What if we can modify our SNI and gain access to different sites? Yes! we can. However, SNI verification will fail, and the connection will be terminated by host. But we still can use ***our own TLS connection(with changed SNI) and use a proxy through it access the internet.***

*Here's a simple diagram showing how it's done.*<br>
<img src="https://github.com/miyurudassanayake/sni-injector/blob/main/static/zoom.us.png" width=50%>

### And here's how is it done

To do so, we need to install a proxy on our server and enable TLS encryption. We can use an SSH tunnel to access a proxy that is already installed on the server. And stunnel can be used to add TLS encryption to that connection.
<img src="https://github.com/miyurudassanayake/sni-injector/blob/main/static/stunnel.png" width="80%">

# Installation

## Windows

1. Clone the repository.<br><br>
2. Install requirements.<br>
   ```console
   pip install -r requirements.txt
   ```
3. Add your SNI host and ssh host to <code>settings.ini </code><br>
   <img src="https://user-images.githubusercontent.com/90369043/184321639-3340d961-8971-43ef-824e-3b47638251b2.png" width="200px"><br>
4. Run Python script.<br>
   ```console
   python3 main.py
   ```
5. Install nmap. *(you need ncat for run this script)*.<br>
   nmap download [page](https://nmap.org/dist/).<br><br>
6. Run ssh command.
   ```console
   ssh -C -o "ProxyCommand=ncat --proxy 127.0.0.1:9092 %h %p" [username]@[host] -p 443 -CND 1080 -o StrictHostKeyChecking=no -o UserKnownHostsFile=nul
   ```
7. Add socks5 proxy and Enjoy!<br>
   <code>host: localhost/127.0.0.1 </code><br>
   <code>port: 1080 </code>

<br>

## Linux

1. Clone the repository.<br>
   ```console
   git clone https://github.com/miyurudassanayake/sni-injector.git
   ```
2. Add your SNI host and ssh host to <code> settings.ini </code><br>
   <img src="https://user-images.githubusercontent.com/90369043/184321639-3340d961-8971-43ef-824e-3b47638251b2.png" width="200px"><br>
3. Run python script. <br>
   ```console
   python3 main.py
   ```
4. Run ssh command. (or run <b>ssh.sh </b> file.)<br>
   ```console
   ssh -C -o "ProxyCommand=nc -X CONNECT -x 127.0.0.1:9092 %h %p" [username]@[host] -p 443 -CND 1080 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null
   ```
   <i>or </i><br>
   ```console
   sshpass -p [password] ssh -C -o "ProxyCommand=nc -X CONNECT -x 127.0.0.1:9092 %h %p" [username]@[host] -p 443 -v -CND 1080 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null
   ```
5. Add socks5 proxy and Enjoy!<br>
   <code>host: localhost/127.0.0.1 </code><br>
   <code>port: 1080 </code>

<br>

## Stargazers over time

[![Stargazers over time](https://starchart.cc/miyurudassanayake/sni-injector.svg)](https://github.com/miyurudassanayake/sni-injector)
