FROM docker.elastic.co/logstash/logstash:8.17.2@sha256:7b86ddaf03b6ac359e4f430ed9f54dfcb22570aa1ec0da155166c9377fc15dd2
RUN bin/logstash-plugin install logstash-codec-sflow
RUN bin/logstash-plugin install logstash-output-opensearch
RUN rm /usr/share/logstash/pipeline/logstash.conf
RUN echo xpack.monitoring.enabled: false > /usr/share/logstash/config/logstash.yml
COPY sflow-pipeline.conf /usr/share/logstash/pipeline/sflow-pipeline.conf
ENV LOG_LEVEL=error
