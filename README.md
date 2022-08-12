# ssh-ssl-http-injector

http ssl ssh tunneling socks5 proxy<br>
working on <h4><b>windows, macos, linux</b></h4><br>


# how to use
  1) Add your SNI host and ssh host to <code>settings.ini</code></li><br>
    ![image](https://user-images.githubusercontent.com/90369043/184321639-3340d961-8971-43ef-824e-3b47638251b2.png)<br><br>
  3) Start python script.
  <code>python3 tunnel.py</code>
  2) Run ssh command.<br>
    <pre>ssh -C -o "ProxyCommand=nc -X CONNECT -x 127.0.0.1:9092 %h %p" username@host -p 443 -CND 1080 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null</pre>
  <i>or</i><br>
    <pre>sshpass -p password ssh -C -o "ProxyCommand=nc -X CONNECT -x 127.0.0.1:9092 %h %p" username@1host -p 443 -v -CND 1080 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null</pre><br>

  3) Add socks5 proxy and Enjoy!<br>
  <code>host: 127.0.0.1</code><br>
  <code>port: 1080</code>
