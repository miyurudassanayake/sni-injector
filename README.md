# ssh-ssl-http-injector
http ssl ssh tunneling socks5 proxy<br>
working on <h4><b>windows, macos, linux</b></h4><br>

### What is a SNI?

[***Server Name Indication (SNI)***](https://en.wikipedia.org/wiki/Server_Name_Indication) is an extension to the Transport Layer Security (TLS) computer networking protocol by which a client indicates which hostname it is attempting to connect to at the start of the handshaking process.This allows a server to present one of multiple possible certificates on the same IP address and TCP port number and hence allows multiple secure (HTTPS) websites (or any other service over TLS) to be served by the same IP address without requiring all those sites to use the same certificate [<sup>Read more</sup>](https://en.wikipedia.org/wiki/Server_Name_Indication)

Here's a screenshot of **Wireshark** while I'm attempting to connect to zoom.us via https.
![ssl.handshake.sni](https://github.com/miyurudassanayake/ssh-ssl-http-injector-to-socks5/blob/main/Screenshot%20from%202022-12-12%2018-28-49.png)
As you can see, I applied the <code>ssl.handshake.extensions server name=zoom.us</code> filter to wrieshark to filter ssl handshakes where sni is <code>zoom.us</code>. 


### What is a SNI BUG Host

SNI bug hosts can be in various forms. They can be a packet host, a free CDN host, government portals, zero-rated websites, social media (subscription), and a variety of other sites. They also do a fantastic job of getting over your Internet service provider's firewall. 

If you have a subscription to <code>zoom.us</code> and want to visit Zoom, your ISP's firewall will scan every time your SSL handshake to determine if the SNI is "zoom.us", and if it does, the firewall will enable you to keep that connection free fo charge. When you have a subscription to access internet, this is what happens. 

What if we can modify our SNI and gain access to different sites? Yes! we can. However, SNI verification will fail, and the connection will be terminated by host. And We also have the option of ***our own SSL connection and use a proxy through it access the internet.***
*Here's a simple diagram showing how it's done.*

![option](https://github.com/miyurudassanayake/ssh-ssl-http-injector-to-socks5/blob/main/zoom.us.png)


### How to do it

To do so, we need to install a proxy on our server and enable TLS encryption. We can use an SSH tunnel to access a proxy that is already installed on the server. And stunnel can be used to add TLS encryption to that connection.


# how to use
  1) Add your SNI host and ssh host to <code>settings.ini</code></li><br>
    ![image](https://user-images.githubusercontent.com/90369043/184321639-3340d961-8971-43ef-824e-3b47638251b2.png)<br><br>
  3) Run python script.
  <code>python3 tunnel.py</code>
  2) Run ssh command.<br>
    <pre>ssh -C -o "ProxyCommand=nc -X CONNECT -x 127.0.0.1:9092 %h %p" username@host -p 443 -CND 1080 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null</pre>
  <i>or</i><br>
    <pre>sshpass -p password ssh -C -o "ProxyCommand=nc -X CONNECT -x 127.0.0.1:9092 %h %p" username@1host -p 443 -v -CND 1080 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null</pre><br>

  3) Add socks5 proxy and Enjoy!<br>
  <code>host: 127.0.0.1</code><br>
  <code>port: 1080</code>
