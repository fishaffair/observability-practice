

Разворачивание тестового стенда:
```shell
kind create cluster --config kind-cluster.yaml
kubectl kustomize --enable-helm | kubectl apply --server-side --force-conflicts -f - # иногда требуется запустить 2 раза для правильноно создания crd
python3 ./grafana-org.py # создаем тенантов и организации в Grafana с Datasource
```
