"""
Installation script for AppZ Hosting
"""

import frappe


def after_install():
    """Setup default data after app installation"""
    create_server_plans()
    create_app_templates()
    frappe.db.commit()


def create_server_plans():
    """Create server plans with 5x Hetzner markup

    Pricing: USD = (Hetzner EUR in USD) × 5
    INR/BTC discounts applied at invoicing via Simbotix
    No pre-provisioning - servers created only on customer delivery
    """

    EUR_TO_USD = 1.05  # Exchange rate

    def calc_price(cost_eur):
        """Calculate USD from Hetzner EUR cost"""
        return round(cost_eur * EUR_TO_USD * 5)

    plans = [
        # Cloud Servers (Hetzner Cloud - Shared vCPU)
        {
            "plan_name": "starter",
            "title": "Starter",
            "category": "cloud",
            "provider": "Hetzner",
            "provider_server_type": "cx22",
            "cpu_cores": 2,
            "ram_gb": 4,
            "storage_gb": 40,
            "bandwidth_tb": 20,
            "max_apps": 2,
            "description": "Dev/staging, small apps",
            "cost_eur": 3.49,
        },
        {
            "plan_name": "growth",
            "title": "Growth",
            "category": "cloud",
            "provider": "Hetzner",
            "provider_server_type": "cx32",
            "cpu_cores": 4,
            "ram_gb": 8,
            "storage_gb": 80,
            "bandwidth_tb": 20,
            "max_apps": 3,
            "description": "Small production, WordPress, Ghost",
            "cost_eur": 5.49,
        },
        {
            "plan_name": "scale",
            "title": "Scale",
            "category": "cloud",
            "provider": "Hetzner",
            "provider_server_type": "cx42",
            "cpu_cores": 8,
            "ram_gb": 16,
            "storage_gb": 160,
            "bandwidth_tb": 20,
            "max_apps": 5,
            "description": "Multiple apps, growing workloads",
            "cost_eur": 9.49,
        },
        # Pro Servers (Hetzner Cloud CCX - Dedicated vCPU)
        {
            "plan_name": "pro",
            "title": "Pro",
            "category": "pro",
            "provider": "Hetzner",
            "provider_server_type": "ccx23",
            "cpu_cores": 4,
            "ram_gb": 16,
            "storage_gb": 160,
            "bandwidth_tb": 20,
            "max_apps": 5,
            "description": "ERPNext single-tenant, production databases",
            "cost_eur": 24.49,
        },
        {
            "plan_name": "business",
            "title": "Business",
            "category": "pro",
            "provider": "Hetzner",
            "provider_server_type": "ccx33",
            "cpu_cores": 8,
            "ram_gb": 32,
            "storage_gb": 240,
            "bandwidth_tb": 20,
            "max_apps": 10,
            "description": "ERPNext + multiple apps, consistent performance",
            "cost_eur": 48.49,
        },
        {
            "plan_name": "enterprise",
            "title": "Enterprise",
            "category": "pro",
            "provider": "Hetzner",
            "provider_server_type": "ccx43",
            "cpu_cores": 16,
            "ram_gb": 64,
            "storage_gb": 360,
            "bandwidth_tb": 20,
            "max_apps": 15,
            "description": "Heavy workloads, large databases",
            "cost_eur": 96.49,
        },
        # Dedicated Servers (Hetzner Robot - Bare Metal)
        {
            "plan_name": "metal",
            "title": "Metal",
            "category": "dedicated",
            "provider": "Hetzner",
            "provider_server_type": "ax41",
            "cpu_cores": 6,
            "ram_gb": 64,
            "storage_gb": 1024,
            "bandwidth_tb": 20,
            "max_apps": 15,
            "description": "Ryzen 5, bare metal entry",
            "cost_eur": 37,
        },
        {
            "plan_name": "metal-pro",
            "title": "Metal Pro",
            "category": "dedicated",
            "provider": "Hetzner",
            "provider_server_type": "ax42",
            "cpu_cores": 8,
            "ram_gb": 64,
            "storage_gb": 1024,
            "bandwidth_tb": 20,
            "max_apps": 20,
            "description": "Ryzen 7 PRO, ideal for Frappe Press",
            "cost_eur": 49,
        },
        {
            "plan_name": "metal-max",
            "title": "Metal Max",
            "category": "dedicated",
            "provider": "Hetzner",
            "provider_server_type": "ax102",
            "cpu_cores": 16,
            "ram_gb": 128,
            "storage_gb": 4000,
            "bandwidth_tb": 20,
            "max_apps": 30,
            "description": "Ryzen 9, multi-tenant hosting",
            "cost_eur": 110,
        },
        {
            "plan_name": "metal-ultra",
            "title": "Metal Ultra",
            "category": "dedicated",
            "provider": "Hetzner",
            "provider_server_type": "ax162",
            "cpu_cores": 48,
            "ram_gb": 256,
            "storage_gb": 8000,
            "bandwidth_tb": 20,
            "max_apps": 50,
            "description": "EPYC, enterprise scale",
            "cost_eur": 210,
        },
    ]

    for plan_data in plans:
        # Calculate USD price from Hetzner cost
        cost_eur = plan_data.pop("cost_eur")
        plan_data["price_usd"] = calc_price(cost_eur)

        if not frappe.db.exists("Server Plan", plan_data["plan_name"]):
            doc = frappe.get_doc({"doctype": "Server Plan", **plan_data})
            doc.insert(ignore_permissions=True)


def create_app_templates():
    """Create default app templates"""
    templates = [
        {
            "template_name": "wordpress",
            "title": "WordPress",
            "category": "CMS",
            "version": "6.4",
            "min_ram_mb": 512,
            "min_storage_gb": 5,
            "internal_port": 80,
            "healthcheck_path": "/",
            "requires_database": 1,
            "database_type": "MySQL",
            "description": "Blog, business website, or CMS",
            "docker_compose": """version: '3'
services:
  app:
    image: wordpress:latest
    container_name: {{ container_name }}
    restart: unless-stopped
    ports:
      - "{{ port }}:80"
    environment:
      WORDPRESS_DB_HOST: db
      WORDPRESS_DB_NAME: wordpress
      WORDPRESS_DB_USER: wordpress
      WORDPRESS_DB_PASSWORD: {{ db_password }}
    volumes:
      - ./html:/var/www/html
    depends_on:
      - db

  db:
    image: mariadb:10
    container_name: {{ container_name }}-db
    restart: unless-stopped
    environment:
      MYSQL_DATABASE: wordpress
      MYSQL_USER: wordpress
      MYSQL_PASSWORD: {{ db_password }}
      MYSQL_ROOT_PASSWORD: {{ db_root_password }}
    volumes:
      - ./mysql:/var/lib/mysql
""",
        },
        {
            "template_name": "n8n",
            "title": "n8n",
            "category": "Automation",
            "version": "latest",
            "min_ram_mb": 1024,
            "min_storage_gb": 5,
            "internal_port": 5678,
            "healthcheck_path": "/healthz",
            "requires_database": 1,
            "database_type": "PostgreSQL",
            "description": "Workflow automation platform",
            "docker_compose": """version: '3'
services:
  app:
    image: n8nio/n8n:latest
    container_name: {{ container_name }}
    restart: unless-stopped
    ports:
      - "{{ port }}:5678"
    environment:
      DB_TYPE: postgresdb
      DB_POSTGRESDB_HOST: db
      DB_POSTGRESDB_DATABASE: n8n
      DB_POSTGRESDB_USER: n8n
      DB_POSTGRESDB_PASSWORD: {{ db_password }}
      N8N_BASIC_AUTH_ACTIVE: "true"
      N8N_BASIC_AUTH_USER: admin
      N8N_BASIC_AUTH_PASSWORD: {{ admin_password }}
      WEBHOOK_URL: https://{{ domain }}/
    volumes:
      - ./n8n:/home/node/.n8n
    depends_on:
      - db

  db:
    image: postgres:14
    container_name: {{ container_name }}-db
    restart: unless-stopped
    environment:
      POSTGRES_DB: n8n
      POSTGRES_USER: n8n
      POSTGRES_PASSWORD: {{ db_password }}
    volumes:
      - ./postgres:/var/lib/postgresql/data
""",
        },
        {
            "template_name": "ghost",
            "title": "Ghost",
            "category": "CMS",
            "version": "5",
            "min_ram_mb": 512,
            "min_storage_gb": 5,
            "internal_port": 2368,
            "healthcheck_path": "/",
            "requires_database": 1,
            "database_type": "MySQL",
            "description": "Modern publishing platform",
            "docker_compose": """version: '3'
services:
  app:
    image: ghost:5
    container_name: {{ container_name }}
    restart: unless-stopped
    ports:
      - "{{ port }}:2368"
    environment:
      url: https://{{ domain }}
      database__client: mysql
      database__connection__host: db
      database__connection__database: ghost
      database__connection__user: ghost
      database__connection__password: {{ db_password }}
    volumes:
      - ./content:/var/lib/ghost/content
    depends_on:
      - db

  db:
    image: mariadb:10
    container_name: {{ container_name }}-db
    restart: unless-stopped
    environment:
      MYSQL_DATABASE: ghost
      MYSQL_USER: ghost
      MYSQL_PASSWORD: {{ db_password }}
      MYSQL_ROOT_PASSWORD: {{ db_root_password }}
    volumes:
      - ./mysql:/var/lib/mysql
""",
        },
        {
            "template_name": "gitea",
            "title": "Gitea",
            "category": "Development",
            "version": "latest",
            "min_ram_mb": 256,
            "min_storage_gb": 10,
            "internal_port": 3000,
            "healthcheck_path": "/",
            "requires_database": 1,
            "database_type": "PostgreSQL",
            "description": "Lightweight Git hosting",
            "docker_compose": """version: '3'
services:
  app:
    image: gitea/gitea:latest
    container_name: {{ container_name }}
    restart: unless-stopped
    ports:
      - "{{ port }}:3000"
      - "{{ ssh_port }}:22"
    environment:
      DB_TYPE: postgres
      DB_HOST: db:5432
      DB_NAME: gitea
      DB_USER: gitea
      DB_PASSWD: {{ db_password }}
    volumes:
      - ./data:/data
    depends_on:
      - db

  db:
    image: postgres:14
    container_name: {{ container_name }}-db
    restart: unless-stopped
    environment:
      POSTGRES_DB: gitea
      POSTGRES_USER: gitea
      POSTGRES_PASSWORD: {{ db_password }}
    volumes:
      - ./postgres:/var/lib/postgresql/data
""",
        },
        {
            "template_name": "postgresql",
            "title": "PostgreSQL",
            "category": "Database",
            "version": "14",
            "min_ram_mb": 512,
            "min_storage_gb": 10,
            "internal_port": 5432,
            "healthcheck_path": "",
            "requires_database": 0,
            "description": "PostgreSQL database server",
            "docker_compose": """version: '3'
services:
  db:
    image: postgres:14
    container_name: {{ container_name }}
    restart: unless-stopped
    ports:
      - "{{ port }}:5432"
    environment:
      POSTGRES_DB: {{ db_name }}
      POSTGRES_USER: {{ db_user }}
      POSTGRES_PASSWORD: {{ db_password }}
    volumes:
      - ./data:/var/lib/postgresql/data
""",
        },
    ]

    for template_data in templates:
        if not frappe.db.exists("App Template", template_data["template_name"]):
            doc = frappe.get_doc({"doctype": "App Template", **template_data})
            doc.insert(ignore_permissions=True)
