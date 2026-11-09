# Validering – 10. november 2026

## Gennemført lokalt

- JSON-parsing, unikke slugs, versionformat, option/schema-overensstemmelse og forskellige standardporte kontrolleret for begge apps.
- Dockerfiles kontrolleret for de korrekte officielle alpine-latest images.
- Manuel gennemgang af agentspecifik konfiguration: Agent bruger AllowRoot, PidFile og StartAgents=0 uden passive checks; Agent 2 bruger ControlSocket og Docker-plugin. PSK og kontroltegn valideres før agentstart. Ingen eval af brugerinput.
- Shellfiler gemt som LF; .gitattributes fastholder formatet.

## Ikke gennemført

Ingen Docker til rådighed lokalt: builds, shell/jq-runtime, agent-opstart, Home Assistant-schema, TLS-forbindelser og reelle målinger er ikke afprøvet. GitHub Actions er klargjort, men er ikke kørt eller uploadet herfra. En grøn CI-test vil heller ikke erstatte Supervisor- og Zabbix-integrationstest.

## Reproducerbar containertest

På Linux med Docker og jq, fra repository-roden, for hver app:

    docker build --pull --no-cache -t ha-zabbix-test zabbix_agent
    sh tests/smoke.sh zabbix_agent
    docker build --pull --no-cache -t ha-zabbix-test zabbix_agent2
    sh tests/smoke.sh zabbix_agent2

GitHub-workflowen kører samme test på amd64 og arm64. Testen undersøger aktive/passive checks, PSK-opstart, agent.ping samt ugyldig PSK og manglende server. Den beviser ikke netværks-TLS-handshake eller korrektheden af værtsmålinger.

## Test på Home Assistant før almindelig brug

1. Installer hver app gennem repositoryet. Kontrollér build, log og agent.version; verificér stabil upstream-version.
2. Bekræft aktive checks i Zabbix og at aktiv-only ikke lytter på en passiv port.
3. Test passive checks fra tilladt og afvist adresse, inkl. de valgte lytteporte.
4. Kør begge apps samtidig med forskellige Zabbix-hostnavne og porte.
5. Test Agent 2's container-discovery og statistik. Sammenhold proces-, netværks-, CPU- og hukommelsesdata med værten. Tilpas filsystem-discovery.
6. Test PSK med korrekt nøgle, forkert nøgle og ukrypteret forbindelse. De sidste to skal afvises i PSK-tilstand.
7. Test genstart, stop, værtsgenstart og backup. Kontrollér manglende data og at hemmeligheder ikke logges.
8. Genopbyg efter upstream-opdatering og verificér den nye version og template-kompatibilitet.

Ingen produktionsklarhed er erklæret.
