## OpenTemetry stack

- openobserve
- alloy
- opentelemetry-collector
- hotrod
- telemetrygen

Пример парсинга логов, метрик, трейсов от приложения Jaeger Hotrod с помощью единого агента `Grafana Alloy` - всё отправляется в `openobserve`.

### Запуск c использованием Alloy

```bash
docker compose --profile openobserve --profile alloy up
```

### Запуск с использованием Opentelemetry Collector (без multitenant)

```bash
docker compose --profile openobserve --profile otlp-collector up
```

### Запуск с Grafana Tempo и Vector в Multitenant режиме


```bash
docker compose --profile vector --profile tempo up

# Генерируем OTEL трейсы:

docker run --network otlp --rm -it ghcr.io/open-telemetry/opentelemetry-collector-contrib/telemetrygen:latest traces --otlp-insecure --duration 5s --otlp-http --otlp-endpoint vector:4318 --otlp-attributes tenant.name=\"floral\"
# Тут используем в качестве метки тенанта OTLP атрибуты
```

### Запуск с использование Opentelemetry Collector в Multitenant режиме:
```bash
docker compose --profile otlp-collector-multitenant --profile tempo up

# Генерируем OTEL трейсы:
# Тут используем в качестве метки тенанта уже OTLP Headers - более предпочтительный способ.
docker run --network otlp --rm -it ghcr.io/open-telemetry/opentelemetry-collector-contrib/telemetrygen:latest traces --otlp-insecure --duration 5s --otlp-http --otlp-endpoint collector:4318 --otlp-header x-tenant-name=\"entity\"

```
