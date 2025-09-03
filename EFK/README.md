# EFK Stack

- elasticsearch
- kibana
- filebeat
- heartbeat

Запуск:
```bash
docker compose -f ../GAP-1/ghost-stack.yaml -p ghost up -d
docker compose -p efk up -d
docker exec -ti elasticsearch /usr/share/elasticsearch/bin/elasticsearch-reset-password -u kibana
```

## Filebeat

![filebeat](./img/filebeat.png)

## Heartbeat

![heartbeat](./img/heartbeat.png)

## Metricbeat

![metricbeat](./img/metricbeat.png)