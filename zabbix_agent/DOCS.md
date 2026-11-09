# Opsætning

Se [installationsvejledning og konfiguration](https://github.com/Kimax89/HA-Zabbix-Agent#readme).

Udfyld hostname og mindst ét serverfelt. Passive checks bruger listen_port. Slå beskyttelsestilstand fra for værtens processer. Kun Agent 2 får Docker-adgang. Filsystemmålinger kan beskrive containeren.

Begge PSK-felter kræves til kryptering. Uden PSK er trafikken ukrypteret. Standardporten er 10052 for Agent og 10050 for Agent 2. Brug forskellige hostnavne og porte, hvis begge køres samtidig.

Appen anvender upstreams stabile alpine-latest. Genopbyg for at hente et nyere image; genstart er ikke nok.
