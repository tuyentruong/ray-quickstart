@echo off

set ip_address_string="IPv4 Address"
for /f "usebackq tokens=2 delims=:" %%i in (`ipconfig ^| findstr /c:%ip_address_string%`) do (
    set IP_ADDRESS=%%i
    goto NEXT
)

:NEXT

ray.exe start --head --node-ip-address %IP_ADDRESS% --port 6380 --ray-client-server-port 10001 --dashboard-host 0.0.0.0 --dashboard-port 8265 --disable-usage-stats
