## Kafka + Vector

Демонстрация работы Kafka с Vector для обработки логов.

Запуск:

```shell
./gen-cert.sh
docker compose up -d
```

Проверка, что Kafka кластер работает:

```bash
kafka-topics --list --bootstrap-server kafka:9093 --command-config /etc/client.properties
kafka-broker-api-versions --bootstrap-server kafka:9093 --command-config /etc/client.properties
```
