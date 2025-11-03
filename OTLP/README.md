## OpenTemetry stack

- openobserve
- alloy
- opentelemetry-collector
- hotrod

Пример парсинга логов, метрик, трейсов от приложения Jaeger Hotrod с помощью единого агента `Grafana Alloy` - всё отправляется в `openobserve`.

### Запуск c использованием Alloy

```bash
docker compose --profile openobserve --profile alloy up
```

### Запуск с использованием Opentelemetry Collector

```bash
docker compose --profile openobserve --profile otlp-collector up
```

### Запуск с Grafana Tempo и Vector в multitenant режиме


```bash
docker compose --profile vector --profile tempo up
```

Генерируем `OTEL` трейсы:

```bash
docker run --network otlp --rm -it ghcr.io/open-telemetry/opentelemetry-collector-contrib/telemetrygen:latest traces --otlp-insecure --duration 5s --otlp-http --otlp-endpoint vector:4318 --otlp-attributes tenant.name=\"floral\"
```