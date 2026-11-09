# Zabbix Agent og Zabbix Agent 2 til Home Assistant

Repository: https://github.com/Kimax89/HA-Zabbix-Agent

To selvstændige Home Assistant-apps, appversion **0.0.2.0**:

| App | Officielt base-image | Standardport for passive checks | Docker-plugin |
| --- | --- | --- | --- |
| Zabbix Agent | `zabbix/zabbix-agent:alpine-latest` | 10052 | Nej |
| Zabbix Agent 2 | `zabbix/zabbix-agent2:alpine-latest` | 10050 | Ja |

Begge følger den nyeste stabile Alpine-variant, ikke `alpine-trunk`. Den konkrete Zabbix-version afhænger af det image, Zabbix har publiceret ved build. Docker Hubs beskrivelser var ikke indbyrdes opdaterede ved kontrollen 10. november 2026; derfor erklærer vi ikke et bestemt patchnummer for begge images. Se agentens opstartslog eller `agent.version` for den faktisk installerede version.

## Installation fra GitHub

1. Upload `repository.yaml`, begge appmapper og de øvrige projektfiler til roden af det offentlige repository. Upload de udpakkede filer, ikke ZIP-filen. `.github` indeholder automatiske buildtests og skal også med.
2. I Home Assistant: **Indstillinger → Apps → Appbutik → ⋮ → Repositorier**. Ældre brugerflader bruger navnet Tilføjelser.
3. Tilføj `https://github.com/Kimax89/HA-Zabbix-Agent` og installer den ønskede app. Home Assistant bygger den lokalt og skal kunne hente Docker-images og Alpine-pakker.
4. Slå **Beskyttelsestilstand / Protection mode** fra for adgang til værtens processer. Agent 2 kræver det også for Docker-socket.
5. Angiv konfigurationen og start appen. Kontrollér loggen.

Kræver Supervisor og appbutik, normalt Home Assistant OS. Home Assistant Container alene understøtter ikke installation af apps. Til lokal installation kan mapperne i stedet kopieres til `/addons/zabbix_agent` og `/addons/zabbix_agent2`.

## Konfiguration

Eksempel for Agent 2:

```yaml
hostname: homeassistant
server_active: "192.168.1.20:10051"
server_passive: ""
listen_port: 10050
tls_psk_identity: ""
tls_psk: ""
```

Erstat serveradressen. For den klassiske Agent bruges som udgangspunkt `hostname: homeassistant-agent` og `listen_port: 10052`. Hvis begge apps kører samtidig, skal deres Zabbix-hostnavne og passive lytteporte være forskellige.

- `hostname`: præcis samme hostnavn som i Zabbix, inklusive store/små bogstaver.
- `server_active`: server/proxy med valgfri port, normalt 10051. Tom betyder ingen aktive checks.
- `server_passive`: tilladte server-/proxyadresser eller netværk, kommasepareret og uden port. Tom deaktiverer passive checks.
- `listen_port`: værtens TCP-port til passive checks. Den skal være ledig og anvendes i Zabbix-hostens agent-interface. Ignoreres, når passive checks er deaktiveret.
- `tls_psk_identity` og `tls_psk`: udfyld begge for kryptering. Nøglen skal være 32-512 hexadecimale tegn og have lige længde. Indstil samme nøgle, identitet og PSK-forbindelsestyper i Zabbix. Med PSK tillades kun PSK. Nøglen indgår i appens konfiguration/backups. Uden PSK er forbindelsen ukrypteret; brug et betroet netværk eller VPN.

Mindst ét serverfelt skal være udfyldt. Tilknyt en Linux-template med den valgte checktype. Agent 2 kan desuden bruge Zabbix' Docker-template; passive Docker-items kræver passive checks. Tilpas templates til din servers og agents versioner.

## Adgang og målingernes afgrænsning

Begge apps deler PID-, netværks- og hostname-namespace med værten og kører som root. De kan se værtens processer og netværk. CPU-/hukommelsesmålinger skal sammenholdes med værten, da cgroups kan påvirke visse værdier.

Kun Agent 2 får Docker-socket og den indbyggede Docker-plugin til container-discovery/status/statistik. Docker-socket giver omfattende adgang til værten, også når socket er monteret read-only. Den klassiske Agent har ikke Agent 2's Docker-plugin.

Værtens rod-filsystem og SMART-enheder er ikke generelt monteret. Filsystem-, OS- og pakkedata kan beskrive appens container. Gennemgå Linux-templatens discovery og ikke-understøttede items. Fjernkommandoer og egne UserParameters er ikke aktiveret. Apps har ingen webside og bruger ikke Home Assistant API-token.

## Opdateringer og test

`alpine-latest` hentes ved et nyt build. Genstart opdaterer ikke agenten. Vælg **Genopbyg / Rebuild**, når ny upstream-version skal hentes; kontrollér derefter den faktiske version i loggen. Ved builds uden for Home Assistant bruges `docker build --pull --no-cache`. Nye appversioner i repositoryet giver Home Assistant en opdateringsindikator; ændringer i upstream-imaget alene gør ikke.

GitHub Actions bygger begge apps på amd64 og arm64 og kører `tests/smoke.sh`. Testen kontrollerer opstart i aktiv/passiv tilstand, PSK-konfiguration og afvisning af fejl. Den erstatter ikke Home Assistant-integrationstest. Se `VALIDATION.md` for hvad der faktisk er kørt. Begge apps er eksperimentelle.

## Kilder

- https://github.com/zabbix/zabbix-docker
- https://hub.docker.com/r/zabbix/zabbix-agent/
- https://hub.docker.com/r/zabbix/zabbix-agent2/
- https://developers.home-assistant.io/docs/apps/configuration/

Zabbix 7.0 og nyere er AGPL-3.0. Bevar upstreams licensoplysninger ved distribution. Filerne er klargjort lokalt, ikke uploadet til GitHub herfra.
