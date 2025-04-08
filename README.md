# opensearch-iac

## Create Opensearch Cluster

Create 3 servers - 4CPU, 16GB RAM, 2TB DISK, Ubuntu 24.04

Run the following on each server, pay attention to the comments and placeholders <PLACEHOLDER> to replace with your own values

```bash
apt-get update && sudo apt-get -y install lsb-release ca-certificates curl gnupg2
curl -o- https://artifacts.opensearch.org/publickeys/opensearch.pgp | gpg --dearmor --batch --yes -o /usr/share/keyrings/opensearch-keyring
echo "deb [signed-by=/usr/share/keyrings/opensearch-keyring] https://artifacts.opensearch.org/releases/bundle/opensearch/2.x/apt stable main" | tee /etc/apt/sources.list.d/opensearch-2.x.list
apt-get update
env OPENSEARCH_INITIAL_ADMIN_PASSWORD=<ADMIN_PASSWORD_SAME_FOR_ALL_CLUSTER> apt-get install opensearch
systemctl enable opensearch
echo "
path.data: /var/lib/opensearch
path.logs: /var/log/opensearch
network.host: 0.0.0.0
discovery.seed_hosts: ["nopens1:9300", "nopens2:9300", "nopens3:9300"]
cluster.initial_master_nodes: ["nopen1", "nopen2", "nopen3"]
plugins.security.disabled: false
plugins.security.ssl.transport.pemcert_filepath: <SERVER_NAME>.pem
plugins.security.ssl.transport.pemkey_filepath: <SERVER_NAME>-key.pem
plugins.security.ssl.http.pemcert_filepath: <SERVER_NAME>.pem
plugins.security.ssl.http.pemkey_filepath: <SERVER_NAME>-key.pem
plugins.security.ssl.transport.pemtrustedcas_filepath: root-ca.pem
plugins.security.ssl.transport.enforce_hostname_verification: false
plugins.security.ssl.http.enabled: true
plugins.security.ssl.http.pemtrustedcas_filepath: root-ca.pem
plugins.security.authcz.admin_dn:
  - CN=A,O=KAMATERA
plugins.security.nodes_dn:
  - CN=nopens1,O=KAMATERA
  - CN=nopens2,O=KAMATERA
  - CN=nopens3,O=KAMATERA
cluster.name: nopens
node.name: <SERVER_NAME>
" > /etc/opensearch/opensearch.yml

# change -Xms / -Xmx to -Xms8g -Xmx8g (half RAM size)
nano /etc/opensearch/jvm.options
cd /etc/opensearch
rm -f *pem

# run the following on the first server only
openssl genrsa -out root-ca-key.pem 2048
openssl req -new -x509 -sha256 -key root-ca-key.pem -subj "/O=KAMATERA/CN=ROOT" -out root-ca.pem -days 3650
openssl genrsa -out admin-key-temp.pem 2048
openssl pkcs8 -inform PEM -outform PEM -in admin-key-temp.pem -topk8 -nocrypt -v1 PBE-SHA1-3DES -out admin-key.pem
openssl req -new -key admin-key.pem -subj "/O=KAMATERA/CN=A" -out admin.csr
openssl x509 -req -in admin.csr -CA root-ca.pem -CAkey root-ca-key.pem -CAcreateserial -sha256 -out admin.pem -days 3650
rm -f *temp.pem *csr *ext
# on next servers, copy these files from the first server
scp root@nopens1:/etc/opensearch/admin-key.pem root@nopens2:/etc/opensearch
scp root@nopens1:/etc/opensearch/admin.pem root@nopens2:/etc/opensearch
scp root@nopens1:/etc/opensearch/root-ca-key.pem root@nopens2:/etc/opensearch
scp root@nopens1:/etc/opensearch/root-ca.pem root@nopens2:/etc/opensearch
scp root@nopens1:/etc/opensearch/root-ca.srl root@nopens2:/etc/opensearch

# continue on each server
cd /etc/opensearch
chown opensearch:opensearch admin-key.pem admin.pem root-ca-key.pem root-ca.pem root-ca.srl

# run this on each server, set SERVER_NAME to the server name
SERVERNAME=nopens1 &&\
openssl genrsa -out ${SERVERNAME}-key-temp.pem 2048 &&\
openssl pkcs8 -inform PEM -outform PEM -in ${SERVERNAME}-key-temp.pem -topk8 -nocrypt -v1 PBE-SHA1-3DES -out ${SERVERNAME}-key.pem &&\
openssl req -new -key ${SERVERNAME}-key.pem -subj "/O=KAMATERA/CN=${SERVERNAME}" -out ${SERVERNAME}.csr &&\
echo subjectAltName=DNS:${SERVERNAME} > ${SERVERNAME}.ext &&\
openssl x509 -req -in ${SERVERNAME}.csr -CA root-ca.pem -CAkey root-ca-key.pem -CAcreateserial -sha256 -out ${SERVERNAME}.pem -days 3650 -extfile ${SERVERNAME}.ext &&\
rm -f *temp.pem *csr *ext &&\
chown opensearch:opensearch ${SERVERNAME}-key.pem ${SERVERNAME}.pem

# set to the IPs of the hosts
echo '
1.2.3.4 nopens1
1.2.3.4 nopens2
1.2.3.4 nopens3
' >> /etc/hosts
```

Start opensearch on all servers

```bash
ssh root@nopens1 systemctl start opensearch
ssh root@nopens2 systemctl start opensearch
ssh root@nopens3 systemctl start opensearch
```

Check cluster status

```bash
curl -u admin:<ADMIN_PASSWORD> https://nopens1:9200/_cluster/health
```

Should show status green and 3 nodes

## Create OpenSearch Dashboards server

Create 1 server - 4 CPU, 16GB RAM, 2TB DISK, Ubuntu 24.04

```bash
apt-get update && sudo apt-get -y install lsb-release ca-certificates curl gnupg2
curl -o- https://artifacts.opensearch.org/publickeys/opensearch.pgp | gpg --dearmor --batch --yes -o /usr/share/keyrings/opensearch-keyring
echo "deb [signed-by=/usr/share/keyrings/opensearch-keyring] https://artifacts.opensearch.org/releases/bundle/opensearch-dashboards/2.x/apt stable main" | tee /etc/apt/sources.list.d/opensearch-dashboards-2.x.list
apt-get update
apt-get install opensearch-dashboards
systemctl enable opensearch-dashboards
echo '
server.host: "0.0.0.0" 
server.name: "nopensdash"
opensearch.hosts: ["https://nopens1:9200", "https://nopens2:9200", "https://nopens3:9200"]
opensearch.username: ""
opensearch.password: ""
server.ssl.enabled: true
server.ssl.certificate: /etc/opensearch-dashboards/nopensdash.pem
server.ssl.key: /etc/opensearch-dashboards/nopensdash-key.pem
opensearch.ssl.certificateAuthorities:
  - /etc/opensearch-dashboards/root-ca.pem
opensearch.requestHeadersWhitelist: [authorization, securitytenant]
' > /etc/opensearch-dashboards/opensearch_dashboards.yml
```

Copy SSL from first server

```
scp root@nopens1:/etc/opensearch/admin-key.pem root@nopensdash:/etc/opensearch-dashboards/
scp root@nopens1:/etc/opensearch/admin.pem root@nopensdash:/etc/opensearch-dashboards/
scp root@nopens1:/etc/opensearch/root-ca-key.pem root@nopensdash:/etc/opensearch-dashboards/
scp root@nopens1:/etc/opensearch/root-ca.pem root@nopensdash:/etc/opensearch-dashboards/
scp root@nopens1:/etc/opensearch/root-ca.srl root@nopensdash:/etc/opensearch-dashboards/
```

Continue on the server

```bash
cd /etc/opensearch-dashboards
chown opensearch-dashboards:opensearch-dashboards admin-key.pem admin.pem root-ca-key.pem root-ca.pem root-ca.srl
SERVERNAME=nopensdash &&\
openssl genrsa -out ${SERVERNAME}-key-temp.pem 2048 &&\
openssl pkcs8 -inform PEM -outform PEM -in ${SERVERNAME}-key-temp.pem -topk8 -nocrypt -v1 PBE-SHA1-3DES -out ${SERVERNAME}-key.pem &&\
openssl req -new -key ${SERVERNAME}-key.pem -subj "/O=KAMATERA/CN=${SERVERNAME}" -out ${SERVERNAME}.csr &&\
echo subjectAltName=DNS:${SERVERNAME} > ${SERVERNAME}.ext &&\
openssl x509 -req -in ${SERVERNAME}.csr -CA root-ca.pem -CAkey root-ca-key.pem -CAcreateserial -sha256 -out ${SERVERNAME}.pem -days 3650 -extfile ${SERVERNAME}.ext &&\
rm -f *temp.pem *csr *ext &&\
chown opensearch-dashboards:opensearch-dashboards ${SERVERNAME}-key.pem ${SERVERNAME}.pem

systemctl start opensearch-dashboards

echo '
1.2.3.4 nopensdash
1.2.3.4 nopens1
1.2.3.4 nopens2
1.2.3.4 nopens3
' >> /etc/hosts
```

https://nopensdash:5601

## Create OpenSearch Anomaly Detection server

Create 1 server - 16 CPU, 64GB RAM, 2TB DISK, Ubuntu 24.04

Run the following on each server, pay attention to the comments and placeholders <PLACEHOLDER> to replace with your own values

```bash
apt-get update && sudo apt-get -y install lsb-release ca-certificates curl gnupg2
curl -o- https://artifacts.opensearch.org/publickeys/opensearch.pgp | gpg --dearmor --batch --yes -o /usr/share/keyrings/opensearch-keyring
echo "deb [signed-by=/usr/share/keyrings/opensearch-keyring] https://artifacts.opensearch.org/releases/bundle/opensearch/2.x/apt stable main" | tee /etc/apt/sources.list.d/opensearch-2.x.list
apt-get update
env OPENSEARCH_INITIAL_ADMIN_PASSWORD=<ADMIN_PASSWORD_SAME_FOR_ALL_CLUSTER> apt-get install opensearch
systemctl enable opensearch
echo "
path.data: /var/lib/opensearch
path.logs: /var/log/opensearch
network.host: 0.0.0.0
discovery.type: single-node
plugins.security.disabled: false
plugins.security.ssl.transport.pemcert_filepath: <SERVER_NAME>.pem
plugins.security.ssl.transport.pemkey_filepath: <SERVER_NAME>-key.pem
plugins.security.ssl.http.pemcert_filepath: <SERVER_NAME>.pem
plugins.security.ssl.http.pemkey_filepath: <SERVER_NAME>-key.pem
plugins.security.ssl.transport.pemtrustedcas_filepath: root-ca.pem
plugins.security.ssl.transport.enforce_hostname_verification: false
plugins.security.ssl.http.enabled: true
plugins.security.ssl.http.pemtrustedcas_filepath: root-ca.pem
plugins.security.authcz.admin_dn:
  - CN=A,O=KAMATERA
plugins.security.nodes_dn:
  - CN=nopensad1,O=KAMATERA
cluster.name: nopensad
node.name: <SERVER_NAME>
cluster.remote.nopens.seeds: ["nopens1:9200","nopens2:9200","nopens3:9200"]
" > /etc/opensearch/opensearch.yml

# change -Xms / -Xmx to -Xms32g -Xmx32g (half RAM size)
nano /etc/opensearch/jvm.options
cd /etc/opensearch
rm -f *pem

# copy these files from the nopens1 server
scp root@nopens1:/etc/opensearch/admin-key.pem root@nopensad1:/etc/opensearch
scp root@nopens1:/etc/opensearch/admin.pem root@nopensad1:/etc/opensearch
scp root@nopens1:/etc/opensearch/root-ca-key.pem root@nopensad1:/etc/opensearch
scp root@nopens1:/etc/opensearch/root-ca.pem root@nopensad1:/etc/opensearch
scp root@nopens1:/etc/opensearch/root-ca.srl root@nopensad1:/etc/opensearch

# continue on the nopensad1 server
cd /etc/opensearch
chown opensearch:opensearch admin-key.pem admin.pem root-ca-key.pem root-ca.pem root-ca.srl

# run this on each server, set SERVER_NAME to the server name
SERVERNAME=nopensad1 &&\
openssl genrsa -out ${SERVERNAME}-key-temp.pem 2048 &&\
openssl pkcs8 -inform PEM -outform PEM -in ${SERVERNAME}-key-temp.pem -topk8 -nocrypt -v1 PBE-SHA1-3DES -out ${SERVERNAME}-key.pem &&\
openssl req -new -key ${SERVERNAME}-key.pem -subj "/O=KAMATERA/CN=${SERVERNAME}" -out ${SERVERNAME}.csr &&\
echo subjectAltName=DNS:${SERVERNAME} > ${SERVERNAME}.ext &&\
openssl x509 -req -in ${SERVERNAME}.csr -CA root-ca.pem -CAkey root-ca-key.pem -CAcreateserial -sha256 -out ${SERVERNAME}.pem -days 3650 -extfile ${SERVERNAME}.ext &&\
rm -f *temp.pem *csr *ext &&\
chown opensearch:opensearch ${SERVERNAME}-key.pem ${SERVERNAME}.pem

# set to the IP of the hosts
echo '
1.2.3.4 nopensad1
1.2.3.4 nopens1
1.2.3.4 nopens2
1.2.3.4 nopens3
' >> /etc/hosts
```

SSH to each of the nopens* servers and modify their opensearch.yml to add the following to `plugins.security.nodes_dn:`:
`- CN=nopensad1,O=KAMATERA`, then restart opensearch on them

Start opensearch on the server

```bash
ssh root@nopensad1 systemctl start opensearch
```

Check cluster status

```bash
curl -ku admin:<ADMIN_PASSWORD> https://nopensad1:9200/_cluster/health
```

Should show status yellow and 1 node

Continue to install OpenSearch Dashboards on nopensad1 server

```bash
echo "deb [signed-by=/usr/share/keyrings/opensearch-keyring] https://artifacts.opensearch.org/releases/bundle/opensearch-dashboards/2.x/apt stable main" | tee /etc/apt/sources.list.d/opensearch-dashboards-2.x.list
apt-get update
apt-get install opensearch-dashboards
systemctl enable opensearch-dashboards
echo '
server.host: "0.0.0.0"
server.name: "nopensad1"
opensearch.hosts: ["https://nopensad1:9200"]
opensearch.username: ""
opensearch.password: ""
server.ssl.enabled: true
server.ssl.certificate: /etc/opensearch-dashboards/nopensad1.pem
server.ssl.key: /etc/opensearch-dashboards/nopensad1-key.pem
opensearch.ssl.certificateAuthorities:
  - /etc/opensearch-dashboards/root-ca.pem
opensearch.requestHeadersWhitelist: [authorization, securitytenant]
' > /etc/opensearch-dashboards/opensearch_dashboards.yml
cd /etc/opensearch-dashboards/
cp /etc/opensearch/nopensad1.pem /etc/opensearch/nopensad1-key.pem /etc/opensearch/root-ca.pem ./
chown opensearch-dashboards:opensearch-dashboards nopensad1-key.pem nopensad1.pem root-ca.pem
systemctl start opensearch-dashboards
```

https://nopensad1:5601
