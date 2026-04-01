from fastapi import FastAPI
from datetime import datetime
import pytz
import json
import os
from prometheus_fastapi_instrumentator import Instrumentator
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.export import ConsoleSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter


def json_span_formatter(span):
    """Format span as single-line JSON."""
    span_data = {
        "name": span.name,
        "context": {
            "trace_id": format(span.context.trace_id, "032x"),
            "span_id": format(span.context.span_id, "016x"),
        },
        "kind": str(span.kind),
        "parent_id": format(span.parent.span_id, "016x") if span.parent else None,
        "start_time": span.start_time,
        "end_time": span.end_time,
        "status": {
            "status_code": str(span.status.status_code),
        },
        "attributes": dict(span.attributes) if span.attributes else {},
    }
    return json.dumps(span_data, default=str)


provider = TracerProvider()
processor = BatchSpanProcessor(ConsoleSpanExporter(formatter=json_span_formatter))
provider.add_span_processor(processor)

# Set up OTLP exporter to send traces to OTEL Collector (default endpoint: localhost:4317)
otlp_exporter = OTLPSpanExporter()
otlp_processor = BatchSpanProcessor(otlp_exporter)
provider.add_span_processor(otlp_processor)

trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)

app = FastAPI()

# Instrument FastAPI with OpenTelemetry
FastAPIInstrumentor.instrument_app(app)

# Instrument the app with Prometheus metrics
Instrumentator().instrument(app).expose(app)

@app.get("/")
async def read_root():
    """
    Root endpoint that provides instructions and a list of available countries.
    """
    countries = {code.upper(): name for code, name in pytz.country_names.items()}
    return {
        "message": "Welcome to FastAPI with async!",
        "instructions": "Use the /localtime/{country} endpoint to get the local time.",
        "available_countries": countries
    }

@app.get("/config")
async def get_config():
    """Demonstrate reading values from ConfigMap and Secret via env vars."""
    return {
        "configmap": {
            "APP_NAME": os.environ.get("APP_NAME", "not set"),
            "APP_ENV": os.environ.get("APP_ENV", "not set"),
            "DEFAULT_TIMEZONE": os.environ.get("DEFAULT_TIMEZONE", "not set"),
        },
        "secret": {
            "API_KEY": os.environ.get("API_KEY", "not set"),
            "DB_PASSWORD": os.environ.get("DB_PASSWORD", "not set"),
        },
    }

@app.get("/pod")
async def get_pod_name():
    """Return the pod name via the HOSTNAME environment variable."""
    return {
        "pod_name": os.environ.get("HOSTNAME", "unknown"),
    }

@app.get("/localtime/{country}")
async def get_local_time(country: str):
    """
    Get the current local time for a specific country.
    
    Args:
        country (str): The ISO 3166-1 alpha-2 country code (e.g., US, FR).
        
    Returns:
        dict: Country name, specific timezone used, and local time.
    """
    try:
        # Get the full name of the country
        country_name = pytz.country_names[country.upper()]
        # Get the timezone(s) for the country (use upper, not lower)
        timezones = pytz.country_timezones.get(country.upper())
        if not timezones:
            return {"error": "No timezone found for this country code"}
        
        # Get the current local time in the first timezone
        # default to the first one available
        selected_timezone = timezones[0]
        local_time = datetime.now(pytz.timezone(selected_timezone))
        return {
            "country": country_name,
            "timezone": selected_timezone,
            "local_time": local_time.strftime("%Y-%m-%d %H:%M:%S")
        }
    except KeyError:
        return {"error": "Invalid country code or timezone not found"}
