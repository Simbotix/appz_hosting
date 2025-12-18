"""
ClickStack Integration for AppZ Hosting

Manages observability addon for customer services.
"""

import frappe
from jinja2 import Template


OTEL_CONFIG_TEMPLATE = """receivers:
  docker_stats:
    endpoint: unix:///var/run/docker.sock
    collection_interval: 30s
    container_labels_to_metric_labels:
      appz.service: service_id
      appz.template: template

  filelog:
    include:
      - /var/lib/docker/containers/*/*.log
    operators:
      - type: json_parser
        timestamp:
          parse_from: attributes.time
          layout: '%Y-%m-%dT%H:%M:%S.%LZ'

processors:
  batch:
    timeout: 10s

  attributes:
    actions:
      - key: tenant_id
        value: {{ tenant_id }}
        action: insert
      - key: service_id
        value: {{ service_id }}
        action: insert

exporters:
  otlphttp:
    endpoint: {{ clickstack_endpoint }}
    headers:
      X-Tenant-ID: {{ tenant_id }}

service:
  pipelines:
    metrics:
      receivers: [docker_stats]
      processors: [batch, attributes]
      exporters: [otlphttp]
    logs:
      receivers: [filelog]
      processors: [batch, attributes]
      exporters: [otlphttp]
"""

OTEL_COMPOSE_TEMPLATE = """  otel-collector:
    image: otel/opentelemetry-collector-contrib:latest
    container_name: {{ service_id }}-otel
    restart: unless-stopped
    command: ["--config=/etc/otel/config.yaml"]
    volumes:
      - {{ data_path }}/otel-config.yaml:/etc/otel/config.yaml:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
    networks:
      - internal
    deploy:
      resources:
        limits:
          memory: 128M
          cpus: '0.1'
"""


def enable_clickstack(service_name):
    """Enable ClickStack observability for a service"""
    service = frappe.get_doc("Hosted Service", service_name)

    # Create tenant if not exists
    tenant_id = get_or_create_tenant(service.customer)

    # Generate OTel config
    otel_config = Template(OTEL_CONFIG_TEMPLATE).render(
        tenant_id=tenant_id,
        service_id=service.name,
        clickstack_endpoint=frappe.conf.get("clickstack_endpoint", "https://otel.appz.studio")
    )

    # Deploy OTel collector
    from appz_hosting.core.deployer import Deployer
    deployer = Deployer(service.server)

    # Upload OTel config
    deployer._upload_file(otel_config, f"/apps/{service.name}/otel-config.yaml")

    # Add OTel sidecar to compose
    otel_compose = Template(OTEL_COMPOSE_TEMPLATE).render(
        service_id=service.name,
        data_path=f"/apps/{service.name}"
    )

    # Read existing compose
    result = deployer._exec(f"cat /apps/{service.name}/docker-compose.yml")
    existing_compose = result["stdout"]

    # Append OTel service (simple approach - in production, use proper YAML merge)
    if "otel-collector" not in existing_compose:
        # Insert before networks section
        if "networks:" in existing_compose:
            parts = existing_compose.rsplit("networks:", 1)
            new_compose = parts[0] + otel_compose + "\nnetworks:" + parts[1]
        else:
            new_compose = existing_compose + "\n" + otel_compose

        deployer._upload_file(new_compose, f"/apps/{service.name}/docker-compose.yml")
        deployer._exec(f"cd /apps/{service.name} && docker compose up -d otel-collector")

    # Create Grafana dashboard
    dashboard_url = create_service_dashboard(service, tenant_id)

    # Create or update observability record
    obs_name = frappe.db.get_value("Service Observability", {"service": service.name})
    if obs_name:
        obs = frappe.get_doc("Service Observability", obs_name)
    else:
        obs = frappe.get_doc({
            "doctype": "Service Observability",
            "service": service.name,
        })

    obs.enabled = 1
    obs.collect_metrics = 1
    obs.collect_logs = 1
    obs.clickstack_tenant = tenant_id
    obs.grafana_dashboard_url = dashboard_url
    obs.monthly_addon_price = 5
    obs.save(ignore_permissions=True)

    # Update service
    service.clickstack_enabled = 1
    service.save(ignore_permissions=True)

    return obs.name


def disable_clickstack(service_name):
    """Disable ClickStack observability"""
    service = frappe.get_doc("Hosted Service", service_name)

    # Remove OTel sidecar
    from appz_hosting.core.deployer import Deployer
    deployer = Deployer(service.server)
    deployer._exec(f"cd /apps/{service.name} && docker compose stop otel-collector && docker compose rm -f otel-collector")

    # Update observability record
    obs_name = frappe.db.get_value("Service Observability", {"service": service.name})
    if obs_name:
        obs = frappe.get_doc("Service Observability", obs_name)
        obs.enabled = 0
        obs.save(ignore_permissions=True)

    # Update service
    service.clickstack_enabled = 0
    service.save(ignore_permissions=True)


def get_or_create_tenant(customer):
    """Get or create ClickStack tenant for customer"""
    # Check if customer already has a tenant
    existing = frappe.db.get_value(
        "Service Observability",
        {"service": ["in", frappe.get_all("Hosted Service", {"customer": customer}, pluck="name")]},
        "clickstack_tenant"
    )
    if existing:
        return existing

    # Generate new tenant ID
    return frappe.generate_hash(customer, 16)


def create_service_dashboard(service, tenant_id):
    """Create Grafana dashboard for service"""
    # In production, this would call Grafana API to provision dashboard
    # For now, return a placeholder URL
    grafana_base = frappe.conf.get("grafana_url", "https://grafana.appz.studio")
    return f"{grafana_base}/d/{service.name}?orgId={tenant_id}"
