#!/usr/bin/env python3
import os
import sys
import json
import copy
import requests
from typing import Optional, Dict, Any, List

GRAFANA_URL = os.environ.get("GRAFANA_URL", "http://localhost:8080").rstrip("/")
GRAFANA_AUTH = os.environ.get("GRAFANA_AUTH", "admin:admin")
ORGS = ["tenant-a", "tenant-b"]
SRC_ORG_ID = int(os.environ.get("SRC_ORG_ID", "1"))
MAIN_ORG_ID = int(os.environ.get("MAIN_ORG_ID", str(SRC_ORG_ID)))
TIMEOUT = 30
UIDS_TO_COPY = ["k8s_views_ns", "k8s_views_pods"]

if ":" not in GRAFANA_AUTH:
    print("GRAFANA_AUTH must be 'user:pass'", file=sys.stderr)
    sys.exit(1)
user, pwd = GRAFANA_AUTH.split(":", 1)

session = requests.Session()
session.auth = (user, pwd)
session.headers.update({"Content-Type": "application/json"})

COLOR_RESET = "\033[0m"
COLORS = {
    "start": "\033[1;32m",
    "org": "\033[1;36m",
    "ds": "\033[1;34m",
    "work": "\033[1;33m",
    "search": "\033[1;35m",
    "found": "\033[1;32m",
    "patch": "\033[1;34m",
    "dash": "\033[1;32m",
    "warn": "\033[1;31m",
    "error": "\033[1;31m",
    "done": "\033[1;32m",
}

def colored(prefix: str) -> str:
    c = COLORS.get(prefix.strip("[]"), "")
    if not c:
        return prefix
    return f"{c}{prefix}{COLOR_RESET}"

def log(prefix: str, msg: str):
    print(f"{colored(prefix)} {msg}")

def log_err(prefix: str, msg: str):
    print(f"{colored(prefix)} {msg}", file=sys.stderr)

def req(method: str, path: str, **kwargs) -> requests.Response:
    url = f"{GRAFANA_URL}{path}"
    return session.request(method, url, timeout=TIMEOUT, **kwargs)

def get_org_id_by_name(name: str) -> Optional[int]:
    r = req("GET", f"/api/orgs/name/{requests.utils.requote_uri(name)}")
    if r.status_code == 200:
        j = r.json()
        return int(j.get("id"))
    return None

def create_org(name: str) -> Optional[int]:
    existing = get_org_id_by_name(name)
    if existing:
        log("[org]", f"exists: '{name}' (id={existing})")
        return existing
    payload = {"name": name}
    r = req("POST", "/api/orgs", json=payload)
    try:
        j = r.json()
    except Exception:
        log_err("[org]", f"create unexpected response for '{name}': {r.status_code} {r.text}")
        return None
    org_id = j.get("orgId") or j.get("orgId")
    if org_id:
        log("[org]", f"created: '{name}' (id={org_id})")
        return int(org_id)
    log_err("[org]", f"failed to create '{name}': {j}")
    return None

def ds_exists(org_id: int, ds_name: str) -> Optional[int]:
    headers = {"X-Grafana-Org-Id": str(org_id)}
    r = req("GET", f"/api/datasources/name/{requests.utils.requote_uri(ds_name)}", headers=headers)
    if r.status_code == 200:
        j = r.json()
        return int(j.get("id"))
    return None

def create_datasource(org_id: int, payload: Dict[str, Any]) -> Optional[int]:
    name = payload.get("name")
    if ds_exists(org_id, name):
        log("[ds]", f"exists: '{name}' in orgId={org_id}")
        return None
    headers = {"X-Grafana-Org-Id": str(org_id)}
    r = req("POST", "/api/datasources", headers=headers, json=payload)
    if r.status_code in (200, 201):
        try:
            j = r.json()
            dsid = j.get("id")
        except Exception:
            dsid = None
        log("[ds]", f"created: '{name}' in orgId={org_id} (id={dsid})")
        return int(dsid) if dsid else None
    try:
        err = r.json()
    except Exception:
        err = r.text
    log_err("[ds]", f"create failed: '{name}' orgId={org_id}: {r.status_code} {err}")
    return None

def get_dashboard_by_uid(src_org_id: int, uid: str) -> Optional[Dict[str, Any]]:
    headers = {"X-Grafana-Org-Id": str(src_org_id)}
    r = req("GET", f"/api/dashboards/uid/{requests.utils.requote_uri(uid)}", headers=headers)
    if r.status_code != 200:
        log_err("[dash]", f"get failed uid={uid}: {r.status_code} {r.text}")
        return None
    return r.json()

def patch_namespace_var(dashboard: Dict[str, Any], target_org_name: str) -> Dict[str, Any]:
    ds_for_var = f"Mimir-{target_org_name}"
    expr = 'label_values(kube_namespace_labels{label_tenant_name=~"${__org.name}"},namespace)'
    templating = dashboard.get("templating") or {}
    vars_list = templating.get("list", []) if isinstance(templating.get("list", []), list) else []
    found = False
    for v in vars_list:
        if v.get("name") == "namespace":
            v["query"] = expr
            v["datasource"] = ds_for_var
            v["type"] = "query"
            found = True
            log("[patch]", f"updated variable 'namespace' datasource->{ds_for_var}")
    if not found:
        new_var = {
            "type": "query",
            "name": "namespace",
            "label": "namespace",
            "query": expr,
            "datasource": ds_for_var,
            "includeAll": False,
            "multi": False
        }
        vars_list.append(new_var)
        log("[patch]", f"added variable 'namespace' datasource->{ds_for_var}")
    templating["list"] = vars_list
    dashboard["templating"] = templating
    return dashboard

def import_dashboard_to_org(target_org_id: int, dashboard: Dict[str, Any], title: str, uid: str) -> bool:
    payload = {"dashboard": dashboard, "overwrite": True}
    headers = {"X-Grafana-Org-Id": str(target_org_id)}
    r = req("POST", "/api/dashboards/db", headers=headers, json=payload)
    if r.status_code in (200, 201):
        log("[dash]", f"imported '{title}' uid={uid} -> orgId={target_org_id}")
        return True
    log_err("[dash]", f"import failed '{title}' uid={uid} -> orgId={target_org_id}: {r.status_code} {r.text}")
    return False

def build_datasource_payloads_for_org(org_name: str) -> List[Dict[str, Any]]:
    mimir_header_value = f"{org_name}|infra"
    return [
        {
            "name": f"Mimir-{org_name}",
            "type": "prometheus",
            "access": "proxy",
            "url": "http://mimir.observability:9009/prometheus",
            "isDefault": False,
            "jsonData": {"httpHeaderName1": "X-Scope-OrgID"},
            "secureJsonData": {"httpHeaderValue1": mimir_header_value},
            "allowUiUpdates": True,
        },
        {
            "name": f"Tempo-{org_name}",
            "type": "tempo",
            "access": "proxy",
            "url": "http://tempo.observability:3200",
            "editable": True,
            "isDefault": False,
            "jsonData": {"httpHeaderName1": "X-Scope-OrgID"},
            "secureJsonData": {"httpHeaderValue1": org_name},
        },
        {
            "name": f"Loki-{org_name}",
            "type": "loki",
            "access": "proxy",
            "url": "http://loki.observability:3100",
            "basicAuth": False,
            "editable": True,
            "jsonData": {"httpHeaderName1": "X-Scope-OrgID"},
            "secureJsonData": {"httpHeaderValue1": org_name},
        },
    ]

def build_main_org_infra_datasources() -> List[Dict[str, Any]]:
    return [
        {
            "name": "Mimir-infra",
            "type": "prometheus",
            "access": "proxy",
            "url": "http://mimir.observability:9009/prometheus",
            "isDefault": False,
            "jsonData": {"httpHeaderName1": "X-Scope-OrgID"},
            "secureJsonData": {"httpHeaderValue1": "infra"},
            "allowUiUpdates": True,
        },
        {
            "name": "Tempo-infra",
            "type": "tempo",
            "access": "proxy",
            "url": "http://tempo.observability:3200",
            "editable": True,
            "isDefault": False,
            "jsonData": {"httpHeaderName1": "X-Scope-OrgID"},
            "secureJsonData": {"httpHeaderValue1": "infra"},
        },
        {
            "name": "Loki-infra",
            "type": "loki",
            "access": "proxy",
            "url": "http://loki.observability:3100",
            "basicAuth": False,
            "editable": True,
            "jsonData": {"httpHeaderName1": "X-Scope-OrgID"},
            "secureJsonData": {"httpHeaderValue1": "infra"},
        },
    ]

def main():
    created_orgs: Dict[str, int] = {}
    log("[start]", f"Grafana={GRAFANA_URL} src_org_id={SRC_ORG_ID} main_org_id={MAIN_ORG_ID}")
    for org in ORGS:
        oid = create_org(org)
        if not oid:
            log_err("[fatal]", f"cannot create/get org {org}")
            sys.exit(1)
        created_orgs[org] = oid
        log("[work]", f"create datasources for org '{org}' (id={oid})")
        for ds_payload in build_datasource_payloads_for_org(org):
            create_datasource(oid, ds_payload)
    log("[work]", f"ensure infra datasources in Main Org id={MAIN_ORG_ID}")
    for ds_payload in build_main_org_infra_datasources():
        create_datasource(MAIN_ORG_ID, ds_payload)
    log("[search]", f"fetching uids list from source org id={SRC_ORG_ID}: {UIDS_TO_COPY}")
    for uid in UIDS_TO_COPY:
        dash_wrapper = get_dashboard_by_uid(SRC_ORG_ID, uid)
        if not dash_wrapper:
            log_err("[warn]", f"cannot fetch uid={uid} from source org id={SRC_ORG_ID}")
            continue
        dashboard = dash_wrapper.get("dashboard")
        if not dashboard:
            log_err("[warn]", f"no dashboard content for uid={uid}")
            continue
        title_local = dashboard.get("title", "<no-title>")
        dashboard.pop("id", None)
        dashboard.pop("version", None)
        for target_org in ORGS:
            target_id = created_orgs.get(target_org)
            if not target_id:
                log("[skip]", f"missing target id for {target_org}")
                continue
            log("[work]", f"importing uid={uid} title='{title_local}' -> org '{target_org}' (id={target_id})")
            patched = patch_namespace_var(copy.deepcopy(dashboard), target_org)
            import_dashboard_to_org(target_id, patched, title_local, uid)
    log("[done]", "")
if __name__ == "__main__":
    try:
        import requests
    except Exception:
        print("Please install requests: pip install requests", file=sys.stderr)
        sys.exit(1)
    main()
