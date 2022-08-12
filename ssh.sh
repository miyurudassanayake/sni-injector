#!/usr/bin/bash

#-Auto login with password
#sshpass -p password ssh -C -o "ProxyCommand=nc -X CONNECT -x 127.0.0.1:9092 %h %p" username@1host -p 443 -v -CND 1080 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null
#-Manual login
#ssh -C -o "ProxyCommand=nc -X CONNECT -x 127.0.0.1:9092 %h %p" username@host -p 443 -CND 1080 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null
