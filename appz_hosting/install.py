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
    """Create default server plans with Simbotix pricing"""
    plans = [
        {
            "plan_name": "starter",
            "title": "Starter",
            "provider": "Hetzner",
            "provider_server_type": "cx32",
            "cpu_cores": 4,
            "ram_gb": 8,
            "storage_gb": 80,
            "bandwidth_tb": 1,
            "max_apps": 3,
            "description": "Perfect for small apps, development, and staging",
            "cost_eur": 7,
            "price_usd": 39,
            "price_inr": 2275,  # 30% off USD
            "price_btc_sats": 23400,  # 40% off USD
        },
        {
            "plan_name": "pro",
            "title": "Pro",
            "provider": "Hetzner",
            "provider_server_type": "ax41",
            "cpu_cores": 8,
            "ram_gb": 64,
            "storage_gb": 1000,
            "bandwidth_tb": 20,
            "max_apps": 10,
            "description": "Production workloads and multiple apps",
            "cost_eur": 49,
            "price_usd": 239,
            "price_inr": 13950,
            "price_btc_sats": 143400,
        },
        {
            "plan_name": "business",
            "title": "Business",
            "provider": "Hetzner",
            "provider_server_type": "ax52",
            "cpu_cores": 8,
            "ram_gb": 64,
            "storage_gb": 2000,
            "bandwidth_tb": 20,
            "max_apps": 20,
            "description": "High-traffic and enterprise workloads",
            "cost_eur": 77,
            "price_usd": 379,
            "price_inr": 22100,
            "price_btc_sats": 227400,
        },
    ]

    for plan_data in plans:
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
