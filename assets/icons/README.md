# App icons

- `zabbix-agent.svg`: white Z on a circular Zabbix-red background.
- `zabbix-agent2.svg`: the same artwork with a white circular badge and red 2 at the lower right.
- Installed app assets: `zabbix_agent/icon.png` and `zabbix_agent2/icon.png`, 256 × 256 RGBA PNG files with transparent corners.

The Z outline and red `#D40000` are derived from [Zabbix's official vector logo reference](https://assets.zabbix.com/img/trademark/logos_570x580.svg). The circular layout and Agent 2 badge are custom artwork for this community Home Assistant repository, not official Zabbix product logos. Zabbix trademarks belong to Zabbix SIA; see the [brand reference](https://www.zabbix.com/trademark).

To regenerate the SVG artwork and PNG files, install Python and Pillow and run `python assets/icons/build_icons.py`. The badge renderer uses Arial Bold or DejaVu Sans Bold. Home Assistant loads each app's `icon.png` automatically; no configuration key is required.
