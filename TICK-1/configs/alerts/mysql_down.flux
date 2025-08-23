import "influxdata/influxdb/monitor"
import "experimental"
import "influxdata/influxdb/v1"

data =
    from(bucket: "telegraf")
        |> range(start: -10m)
        |> filter(fn: (r) => r["_measurement"] == "docker_container_health")
        |> filter(fn: (r) => r["_field"] == "health_status")
        |> filter(fn: (r) => r["container_name"] == "tick-mysql-1")

option task = {name: "mysql_down", every: 1m, offset: 0s}

check = {_check_id: "0f64a8e4ce3d7000", _check_name: "Name this Check", _type: "deadman", tags: {}}
crit = (r) => r["dead"]
messageFn = (r) => "MYSQL container is not healty"

data
    |> v1["fieldsAsCols"]()
    |> monitor["deadman"](t: experimental["subDuration"](from: now(), d: 90s))
    |> monitor["check"](data: check, messageFn: messageFn, crit: crit)
