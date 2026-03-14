## Vector + RabbitMQ

Демонстрация работы RabbitMQ с Vector для обработки логов.

Запуск:

```shell
docker compose up -d
```

Веб панель кластера RabbitMQ будет на порту `15672`

## Схема взаимодействия

```mermaid
graph LR
    LG["Log Generator: flog"]
    VP["Vector Producer"]
    VC["Vector Consumer"]
    FILE["/tmp/flog-routing.log"]

    LG -->|docker logs| VP
    VP -->|AMQP publish JSON<br/>exchange: vector<br/>routing_key: message.method| EX

    subgraph RMQ["RabbitMQ cluster (rabbitmq-cluster)"]
        EX["exchange: vector"]
        QGET["queue: vector_get"]
        QPOST["queue: vector_post"]
        QPUT["queue: vector_put"]
        EX -->|route key: GET| QGET
        EX -->|route key: POST| QPOST
        EX -->|route key: PUT| QPUT
    end

    QGET -->|rabbitmq-1| VC
    QPOST -->|rabbitmq-2| VC
    QPUT -->|rabbitmq-3| VC
    VC -->|parse payload| FILE
```
