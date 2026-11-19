FROM zabbix/zabbix-agent2:alpine-latest
ARG BUILD_VERSION=development
LABEL org.opencontainers.image.title="Zabbix Agent 2 for Home Assistant" \
      org.opencontainers.image.source="https://github.com/Kimax89/HA-Zabbix-Agent" \
      org.opencontainers.image.version="${BUILD_VERSION}"
USER root
RUN apk add --no-cache jq
COPY run.sh /usr/local/bin/ha-zabbix-run
COPY runtime.sh /usr/local/lib/ha-zabbix.sh
RUN chmod 0755 /usr/local/bin/ha-zabbix-run
STOPSIGNAL SIGTERM
ENTRYPOINT ["/bin/sh", "/usr/local/bin/ha-zabbix-run"]
CMD []
