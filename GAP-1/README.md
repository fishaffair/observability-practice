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

Запуск:
```bash
docker compose -f ghost-stack.yaml up
docker compose -f vmetrics-stack.yaml up
docker compose -f exporters-stack.yaml up
```