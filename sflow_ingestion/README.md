# Sflow Ingestion Example

On OpenSearch - create a DataStream:

* Index Management > Templates > Create template
  * Template name: sflow
  * Template type: Data streams
  * Time field: @timestamp
  * Index pattern: sflow-*
  * Primary shards: 3
  * Replica shards: 3
  * Create template
* Data Streams > Create data stream
  * Data stream name: sflow-datastream
  * Template: sflow
  * Create data stream

Start logstash

```
cd sflow_ingestion
docker compose up --build
```

Send sflow data from pcap file:

```
sudo venv/bin/python sflow_ingestion/generate_sflow.py
```