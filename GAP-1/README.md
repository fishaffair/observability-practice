## GAP-1

В качестве CMS был выбран проект [Ghost](https://github.com/TryGhost/Ghost), как альтератива популярного CMS WordPress. База данных -  MySQL. 

Все сервисы работают локально (через locahost) и не выведены наружу портами.

Для мониторинга была выбрана Vicrotia Metrics, так как в будущем она рассматривается и хотелось её сразу применить на практике. Для обнаружения target метрик используется автоматический docker service discovery.

Текущая реализация выглядит так:

* exporters-stack
    - node-exporter
    - mysqld-exporter
    - blackbox-exporter
* vmetrics-stack
    - grafana
    - vicrotiametrics
    - vmagent
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
```
### Запуск
```bash
docker network create observability
docker compose -f exporters-stack.yaml -p exporters up
docker compose -f ghost-stack.yaml -p ghost up
docker compose -f vmetrics-stack.yaml -p vmetrics up
```