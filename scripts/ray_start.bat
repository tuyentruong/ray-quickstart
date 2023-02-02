echo off

ray.exe start --head --node-ip-address 192.168.2.4 --port 6380 --ray-client-server-port 10001 --dashboard-host 0.0.0.0 --dashboard-port 8265 --disable-usage-stats
