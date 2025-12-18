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
        # Cloud Servers (Shared vCPU)
        {
            "plan_name": "cloud-s",
            "title": "Cloud S",
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
            "plan_name": "cloud-m",
            "title": "Cloud M",
            "category": "cloud",
            "provider": "Hetzner",
            "provider_server_type": "cx32",
            "cpu_cores": 4,
            "ram_gb": 8,
            "storage_gb": 80,
            "bandwidth_tb": 20,
            "max_apps": 3,
            "description": "Small production apps",
            "cost_eur": 5.49,
        },
        {
            "plan_name": "cloud-l",
            "title": "Cloud L",
            "category": "cloud",
            "provider": "Hetzner",
            "provider_server_type": "cx42",
            "cpu_cores": 8,
            "ram_gb": 16,
            "storage_gb": 160,
            "bandwidth_tb": 20,
            "max_apps": 5,
            "description": "Medium production apps",
            "cost_eur": 9.49,
        },
        {
            "plan_name": "cloud-xl",
            "title": "Cloud XL",
            "category": "cloud",
            "provider": "Hetzner",
            "provider_server_type": "cx52",
            "cpu_cores": 16,
            "ram_gb": 32,
            "storage_gb": 320,
            "bandwidth_tb": 20,
            "max_apps": 8,
            "description": "Large apps, multiple services",
            "cost_eur": 17.49,
        },
        # Pro Servers (Dedicated vCPU)
        {
            "plan_name": "pro-2",
            "title": "Pro 2",
            "category": "pro",
            "provider": "Hetzner",
            "provider_server_type": "ccx13",
            "cpu_cores": 2,
            "ram_gb": 8,
            "storage_gb": 80,
            "bandwidth_tb": 20,
            "max_apps": 3,
            "description": "Dedicated vCPU for consistent performance",
            "cost_eur": 12.49,
        },
        {
            "plan_name": "pro-4",
            "title": "Pro 4",
            "category": "pro",
            "provider": "Hetzner",
            "provider_server_type": "ccx23",
            "cpu_cores": 4,
            "ram_gb": 16,
            "storage_gb": 160,
            "bandwidth_tb": 20,
            "max_apps": 5,
            "description": "Small ERPNext, production databases",
            "cost_eur": 24.49,
        },
        {
            "plan_name": "pro-8",
            "title": "Pro 8",
            "category": "pro",
            "provider": "Hetzner",
            "provider_server_type": "ccx33",
            "cpu_cores": 8,
            "ram_gb": 32,
            "storage_gb": 240,
            "bandwidth_tb": 20,
            "max_apps": 10,
            "description": "Medium ERPNext, multiple apps",
            "cost_eur": 48.49,
        },
        {
            "plan_name": "pro-16",
            "title": "Pro 16",
            "category": "pro",
            "provider": "Hetzner",
            "provider_server_type": "ccx43",
            "cpu_cores": 16,
            "ram_gb": 64,
            "storage_gb": 360,
            "bandwidth_tb": 20,
            "max_apps": 15,
            "description": "Large ERPNext, heavy workloads",
            "cost_eur": 96.49,
        },
        {
            "plan_name": "pro-32",
            "title": "Pro 32",
            "category": "pro",
            "provider": "Hetzner",
            "provider_server_type": "ccx53",
            "cpu_cores": 32,
            "ram_gb": 128,
            "storage_gb": 600,
            "bandwidth_tb": 20,
            "max_apps": 25,
            "description": "Enterprise workloads, multi-tenant",
            "cost_eur": 192.49,
        },
        # Dedicated Servers (AMD)
        {
            "plan_name": "dedicated-6",
            "title": "Dedicated 6",
            "category": "dedicated",
            "provider": "Hetzner",
            "provider_server_type": "ax41",
            "cpu_cores": 6,
            "ram_gb": 64,
            "storage_gb": 1024,
            "bandwidth_tb": 20,
            "max_apps": 15,
            "description": "Ryzen 5, bare metal performance",
            "cost_eur": 37,
        },
        {
            "plan_name": "dedicated-8",
            "title": "Dedicated 8",
            "category": "dedicated",
            "provider": "Hetzner",
            "provider_server_type": "ax42",
            "cpu_cores": 8,
            "ram_gb": 64,
            "storage_gb": 1024,
            "bandwidth_tb": 20,
            "max_apps": 20,
            "description": "Ryzen 7 PRO, DDR5, ideal for ERPNext",
            "cost_eur": 49,
        },
        {
            "plan_name": "dedicated-16",
            "title": "Dedicated 16",
            "category": "dedicated",
            "provider": "Hetzner",
            "provider_server_type": "ax102",
            "cpu_cores": 16,
            "ram_gb": 128,
            "storage_gb": 4000,
            "bandwidth_tb": 20,
            "max_apps": 30,
            "description": "Ryzen 9, multi-tenant, Frappe Press",
            "cost_eur": 110,
        },
        {
            "plan_name": "dedicated-48",
            "title": "Dedicated 48",
            "category": "dedicated",
            "provider": "Hetzner",
            "provider_server_type": "ax162",
            "cpu_cores": 48,
            "ram_gb": 128,
            "storage_gb": 8000,
            "bandwidth_tb": 20,
            "max_apps": 50,
            "description": "EPYC, enterprise scale",
            "cost_eur": 210,
        },
        # Dedicated Servers (Intel)
        {
            "plan_name": "intel-14",
            "title": "Intel 14",
            "category": "dedicated-intel",
            "provider": "Hetzner",
            "provider_server_type": "ex44",
            "cpu_cores": 14,
            "ram_gb": 64,
            "storage_gb": 1024,
            "bandwidth_tb": 20,
            "max_apps": 15,
            "description": "i5-13500, Intel compatibility",
            "cost_eur": 39,
        },
        {
            "plan_name": "intel-20",
            "title": "Intel 20",
            "category": "dedicated-intel",
            "provider": "Hetzner",
            "provider_server_type": "ex63",
            "cpu_cores": 20,
            "ram_gb": 64,
            "storage_gb": 2000,
            "bandwidth_tb": 20,
            "max_apps": 25,
            "description": "Core Ultra 7, DDR5",
            "cost_eur": 66,
        },
        {
            "plan_name": "intel-24",
            "title": "Intel 24",
            "category": "dedicated-intel",
            "provider": "Hetzner",
            "provider_server_type": "ex130",
            "cpu_cores": 24,
            "ram_gb": 256,
            "storage_gb": 4000,
            "bandwidth_tb": 20,
            "max_apps": 40,
            "description": "Xeon Gold, enterprise Intel",
            "cost_eur": 134,
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
