import "influxdata/influxdb/monitor"
import "influxdata/influxdb/v1"

data =
    from(bucket: "telegraf")
        |> range(start: -1m)
        |> filter(fn: (r) => r["_measurement"] == "http_response")
        |> filter(fn: (r) => r["_field"] == "result_code")
        |> aggregateWindow(every: 1m, fn: mean, createEmpty: false)

option task = {name: "Ghost down", every: 1m, offset: 0s}

check = {_check_id: "0f65f67f616cf000", _check_name: "Ghost down", _type: "threshold", tags: {}}
crit = (r) => r["result_code"] > 1.0
messageFn = (r) => "Ghost CMS down, http code: ${ r._level }"

data |> v1["fieldsAsCols"]() |> monitor["check"](data: check, messageFn: messageFn, crit: crit)