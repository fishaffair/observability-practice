import "influxdata/influxdb/monitor"
import "influxdata/influxdb/v1"

data =
    from(bucket: "docker")
        |> range(start: -15m0s)
        |> filter(fn: (r) => r["_measurement"] == "docker_container_cpu")
        |> filter(fn: (r) => r["_field"] == "usage_percent")
        |> aggregateWindow(every: 15m0s, fn: mean, createEmpty: false)

option task = {name: "Container CPU Usage Pct", every: 15m0s, offset: 0s}

check = {
    _check_id: "0f634f4936c8b000",
    _check_name: "Container CPU Usage Pct",
    _type: "threshold",
    tags: {},
}
warn = (r) => r["usage_percent"] > 80.0
crit = (r) => r["usage_percent"] > 90.0
ok = (r) => r["usage_percent"] < 80.0
messageFn = (r) => "Check: ${ r._check_name } for container {r.container_name} is: ${ r._level }"

data
    |> v1["fieldsAsCols"]()
    |> monitor["check"](
        data: check,
        messageFn: messageFn,
        warn: warn,
        crit: crit,
        ok: ok,
    )
