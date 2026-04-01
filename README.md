# timetime

A FastAPI application that returns local time for any country, with built-in Prometheus metrics and OpenTelemetry tracing.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Welcome page with list of available country codes |
| GET | `/localtime/{country}` | Get local time by ISO 3166-1 alpha-2 country code (e.g., `US`, `TH`, `FR`) |
| GET | `/config` | Show ConfigMap and Secret values injected via environment variables |
| GET | `/pod` | Return the current pod name (from `HOSTNAME`) |
| GET | `/metrics` | Prometheus metrics endpoint (auto-generated) |

## Environment Variables

### ConfigMap (non-sensitive config)

| Variable | Description | Example |
|----------|-------------|---------|
| `APP_NAME` | Application name | `timetime` |
| `APP_ENV` | Environment name | `production` |
| `DEFAULT_TIMEZONE` | Default timezone | `Asia/Bangkok` |

### Secret (sensitive data)

| Variable | Description | Example |
|----------|-------------|---------|
| `API_KEY` | API key for authentication | `my-super-secret-api-key` |
| `DB_PASSWORD` | Database password | `s3cur3P@ssw0rd` |

### OpenTelemetry

| Variable | Description | Default |
|----------|-------------|---------|
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OTLP collector endpoint | `http://localhost:4317` |

## Build

```bash
podman build --platform linux/amd64 -t timetime:latest ./build
```

## Deploy to OpenShift

### Push image to OpenShift registry

```bash
REGISTRY=$(oc get route default-route -n openshift-image-registry -o jsonpath='{.spec.host}')
podman login $REGISTRY -u $(oc whoami) -p $(oc whoami -t) --tls-verify=false
podman tag timetime:latest $REGISTRY/<project-name>/timetime:latest
podman push $REGISTRY/<project-name>/timetime:latest --tls-verify=false
```

### Create ConfigMap and Secret

```bash
oc create configmap timetime-config \
  --from-literal=APP_NAME=timetime \
  --from-literal=APP_ENV=production \
  --from-literal=DEFAULT_TIMEZONE=Asia/Bangkok

oc create secret generic timetime-secret \
  --from-literal=API_KEY=my-super-secret-api-key \
  --from-literal=DB_PASSWORD=s3cur3P@ssw0rd
```

### Deploy the application

```bash
oc new-app <project-name>/timetime:latest --name=timetime
oc set env deployment/timetime --from=configmap/timetime-config
oc set env deployment/timetime --from=secret/timetime-secret
oc expose svc/timetime --port=8000
```

## Project Structure

```
timetime/
├── build/
│   ├── Dockerfile
│   ├── app.py
│   └── requirements.txt
├── deployment/
│   ├── 00-timetime-base.yaml
│   ├── 01-timetime-cm-secret.yaml
│   ├── 02-timetime-nodeselector.yaml
│   └── 03-timetime-toleration
└── README.md
```
