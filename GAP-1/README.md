## GAP-1

В качестве CMS был выбран проект [Ghost](https://github.com/TryGhost/Ghost), как альтератива популярного CMS WordPress. База данных -  MySQL.
Все сервисы работают локально (через locahost) и не выведены наружу портами.
Для обнаружения target метрик используется автоматический docker service discovery. Долгосрочное хранение данных - Grafana Mimir. Алерты - встроенный в [Mimir Alertmanager](https://grafana.com/docs/mimir/latest/references/architecture/components/alertmanager/), полностью совместимый с Prometheus Alertmanager. В качестве сервсиса получения уведомлений - [Zenduty](https://zenduty.com/) через [Webhook](./configs/alertmanager.yaml). 
Nginx (Angie) используется как multitenant-proxy, который преобразует ID организации Grafana в имя тенанта от которого делается PromQL запрос в Mimir через небольшой lua скрипт.

Текущая реализация выглядит так:

* exporters-stack
    - node-exporter
    - mysqld-exporter
    - blackbox-exporter
* metrics-stack
    - grafana
    - prometheus
    - mimir
    - angie
* ghost-stack
    - ghost
    - mysql

Дашборды в Grafana загружаются из папки `dashboards`, которая не включена в репозиторий по причине большого количества JSON кода.

### Настройка

В `.env` необходимо установить параметры:
```bash
GHOST_DB_CLIENT=
GHOST_DB_HOSTNAME=
GHOST_DB_USER=
MYSQL_ROOT_PASSWORD=
GHOST_DB_NAME=
GRAFANA_ADMIN=
GRAFANA_PASSWORD=
MYSQL_ROOT_PASSWORD=
GRAFANA_TOKEN=
```
### Запуск
```bash
docker network create observability
docker compose -f exporters-stack.yaml -p exporters up
docker compose -f ghost-stack.yaml -p ghost up
docker compose -f metrics-stack.yaml -p metrics up
mimirtool rules load ./rules/node-exporter-rules.yaml --address=http://localhost:9009 --id=floral # Загружаем в Mimir tenant rules для алертов
mimirtool alertmanager load ./configs/alertmanager.yaml --address=http://localhost:9009 --id=floral # Загружаем в Mimir tenant конфиг для AlertManager
```