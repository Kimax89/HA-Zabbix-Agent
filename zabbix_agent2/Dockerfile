FROM zabbix/zabbix-agent2:alpine-latest
USER root
RUN apk add --no-cache jq
COPY run.sh /usr/local/bin/ha-zabbix-run
RUN chmod 0755 /usr/local/bin/ha-zabbix-run
ENTRYPOINT ["/bin/sh", "/usr/local/bin/ha-zabbix-run"]
CMD []
