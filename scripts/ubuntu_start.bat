echo off

wsl --terminate Ubuntu-22.04

netsh interface portproxy reset

rem Start Ubuntu "nohup sleep 100000 &" to keep the process running
start /b cmd /c "C:\Windows\system32\wsl.exe -u %USERNAME% -d Ubuntu-22.04 --cd ~/git nohup sleep 100000 &"

set ip_address_string="IPv4 Address"
for /f "usebackq tokens=2 delims=:" %%i in (`ipconfig ^| findstr /c:%ip_address_string%`) do (
    set IP_ADDRESS=%%i
    goto NEXT
)

:NEXT

for /f "tokens=*" %%i IN ('wsl -d Ubuntu-22.04 hostname -I') do set UBUNTU_IP_ADDRESS=%%i

netsh interface portproxy set v4tov4 listenport=22 listenaddress=%IP_ADDRESS% connectport=22 connectaddress=%UBUNTU_IP_ADDRESS% protocol=tcp
netsh interface portproxy set v4tov4 listenport=6380 listenaddress=%IP_ADDRESS% connectport=6380 connectaddress=%UBUNTU_IP_ADDRESS% protocol=tcp
netsh interface portproxy set v4tov4 listenport=8265 listenaddress=%IP_ADDRESS% connectport=8265 connectaddress=%UBUNTU_IP_ADDRESS% protocol=tcp
netsh interface portproxy set v4tov4 listenport=10001 listenaddress=%IP_ADDRESS% connectport=10001 connectaddress=%UBUNTU_IP_ADDRESS% protocol=tcp
netsh interface portproxy set v4tov4 listenport=63344 listenaddress=%IP_ADDRESS% connectport=63344 connectaddress=%UBUNTU_IP_ADDRESS% protocol=tcp

netsh interface portproxy show all
