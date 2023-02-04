setlocal
@echo off

wsl --unregister Ubuntu-22.04
wsl --install Ubuntu-22.04
wsl -u root -d Ubuntu-22.04 -- ls

:ubuntu_not_started
echo Waiting for Ubuntu to start...
wsl -u root -d Ubuntu-22.04 -- ls
if %ERRORLEVEL% == 0 (
    echo Ubuntu-22.04 is running
    goto :ubuntu_started
) else (
    echo Ubuntu-22.04 is not running
    timeout 2 /nobreak > nul
    goto :ubuntu_not_started
)

:ubuntu_started
wsl --terminate Ubuntu-22.04

rem enable password-less sudo
wsl -u root -d Ubuntu-22.04 -- useradd -s /bin/bash -m %USERNAME%
wsl -u root -d Ubuntu-22.04 -- passwd -d %USERNAME%
wsl -u root -d Ubuntu-22.04 -- echo "%USERNAME%    ALL = (ALL) NOPASSWD: ALL" ^> /etc/sudoers.d/%USERNAME%
wsl -u root -d Ubuntu-22.04 -- chmod 0440 /etc/sudoers.d/%USERNAME%

rem create wsl.conf file
wsl -u root -d Ubuntu-22.04 -- echo "[boot]" > /etc/wsl.conf
wsl -u root -d Ubuntu-22.04 -- echo "systemd=true" > /etc/wsl.conf
wsl -u root -d Ubuntu-22.04 -- echo "" > /etc/wsl.conf
wsl -u root -d Ubuntu-22.04 -- echo "[interop]" > /etc/wsl.conf
wsl -u root -d Ubuntu-22.04 -- echo "appendWindowsPath = false" > /etc/wsl.conf
wsl -u root -d Ubuntu-22.04 -- echo "" > /etc/wsl.conf
wsl -u root -d Ubuntu-22.04 -- echo "[wsl2]" > /etc/wsl.conf
wsl -u root -d Ubuntu-22.04 -- echo "vmIdleTimeout=-1" > /etc/wsl.conf


cd %~dp0
wsl -u %USERNAME% ./setup_ubuntu.sh

netsh advfirewall firewall add rule name="SSH Port 22" dir=in action=allow protocol=TCP localport=22

rem Allow Ray ports through Windows Firewall:
netsh advfirewall firewall add rule name="Ray Port 6380" dir=in action=allow protocol=TCP localport=6380
netsh advfirewall firewall add rule name="Ray Dashboard Port 8265" dir=in action=allow protocol=TCP localport=8265
netsh advfirewall firewall add rule name="Ray Client Server Port 10001" dir=in action=allow protocol=TCP localport=10001

endlocal
