netsh interface portproxy reset

REM Start Ubuntu "nohup sleep 100000 &" to keep the process running
START /B CMD /C "C:\Windows\system32\wsl.exe -u %USERNAME% -d Ubuntu-22.04 --cd ~/git nohup sleep 100000 &"

FOR /F "tokens=*" %%i IN ('wsl -d Ubuntu-22.04 hostname -I') DO SET IP_ADDRESS=%%i

netsh interface portproxy set v4tov4 listenport=22 listenaddress=192.168.2.4 connectport=53422 connectaddress=%IP_ADDRESS% protocol=tcp
netsh interface portproxy set v4tov4 listenport=6380 listenaddress=192.168.2.4 connectport=6380 connectaddress=%IP_ADDRESS% protocol=tcp
netsh interface portproxy set v4tov4 listenport=8265 listenaddress=192.168.2.4 connectport=8265 connectaddress=%IP_ADDRESS% protocol=tcp
netsh interface portproxy set v4tov4 listenport=10001 listenaddress=192.168.2.4 connectport=10001 connectaddress=%IP_ADDRESS% protocol=tcp
netsh interface portproxy show all
