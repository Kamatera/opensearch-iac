# Sflow Ingestion Example

```
cd sflow_ingestion
docker compose up -d --build --force-recreate
```

Send TCP data from .pcap file

```
tcprewrite --dstipmap=192.168.0.241:127.0.0.1 -i file.pcap -o file_modified.pcap
tcpreplay -i lo file_modified.pcap
```
