## Vector + Loki

Vector берет логи из Docker демона и отсылает их в Loki, сам Loki запущен в Multitenant режиме, в качестве определителя тенанта используется `label` на docker контейнере `org.tenant.name`.
Дополнительно удаляются лишние поля из `json` тела лога.