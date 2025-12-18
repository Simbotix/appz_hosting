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
    """Create server plans for Hetzner and Vultr

    Pricing: USD = Provider Cost (in USD) × 5
    - Hetzner: Default provider (best value, EU datacenter)
    - Vultr: Used for BTC templates (Hetzner ToS prohibits crypto)

    No pre-provisioning - servers created only on customer delivery
    """

    EUR_TO_USD = 1.05  # Exchange rate

    def calc_price_eur(cost_eur):
        """Calculate USD from EUR cost (Hetzner)"""
        return round(cost_eur * EUR_TO_USD * 5)

    def calc_price_usd(cost_usd):
        """Calculate USD from USD cost (Vultr)"""
        return round(cost_usd * 5)

    plans = [
        # ============================================
        # HETZNER PLANS (Default - best value)
        # ============================================

        # Cloud Servers (Hetzner Cloud CX - Shared vCPU)
        {
            "plan_name": "starter-hetzner",
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
            "cost": 3.49,
            "cost_currency": "EUR",
        },
        {
            "plan_name": "growth-hetzner",
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
            "cost": 5.49,
            "cost_currency": "EUR",
        },
        {
            "plan_name": "scale-hetzner",
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
            "cost": 9.49,
            "cost_currency": "EUR",
        },
        # Pro Servers (Hetzner Cloud CCX - Dedicated vCPU)
        {
            "plan_name": "pro-hetzner",
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
            "cost": 24.49,
            "cost_currency": "EUR",
        },
        {
            "plan_name": "business-hetzner",
            "title": "Business",
            "category": "pro",
            "provider": "Hetzner",
            "provider_server_type": "ccx33",
            "cpu_cores": 8,
            "ram_gb": 32,
            "storage_gb": 240,
            "bandwidth_tb": 20,
            "max_apps": 10,
            "description": "ERPNext + multiple apps",
            "cost": 48.49,
            "cost_currency": "EUR",
        },
        {
            "plan_name": "enterprise-hetzner",
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
            "cost": 96.49,
            "cost_currency": "EUR",
        },
        # Dedicated Servers (Hetzner Robot AX - Bare Metal)
        {
            "plan_name": "metal-hetzner",
            "title": "Metal",
            "category": "dedicated",
            "provider": "Hetzner",
            "provider_server_type": "ax41",
            "cpu_cores": 6,
            "ram_gb": 64,
            "storage_gb": 1024,
            "bandwidth_tb": 20,
            "max_apps": 15,
            "description": "Ryzen 5 3600, bare metal entry",
            "cost": 37,
            "cost_currency": "EUR",
        },
        {
            "plan_name": "metal-pro-hetzner",
            "title": "Metal Pro",
            "category": "dedicated",
            "provider": "Hetzner",
            "provider_server_type": "ax42",
            "cpu_cores": 8,
            "ram_gb": 64,
            "storage_gb": 1024,
            "bandwidth_tb": 20,
            "max_apps": 20,
            "description": "Ryzen 7 PRO 8700GE, ideal for Frappe Press",
            "cost": 49,
            "cost_currency": "EUR",
        },
        {
            "plan_name": "metal-max-hetzner",
            "title": "Metal Max",
            "category": "dedicated",
            "provider": "Hetzner",
            "provider_server_type": "ax102",
            "cpu_cores": 16,
            "ram_gb": 128,
            "storage_gb": 4000,
            "bandwidth_tb": 20,
            "max_apps": 30,
            "description": "Ryzen 9 7950X3D, multi-tenant hosting",
            "cost": 110,
            "cost_currency": "EUR",
        },
        {
            "plan_name": "metal-ultra-hetzner",
            "title": "Metal Ultra",
            "category": "dedicated",
            "provider": "Hetzner",
            "provider_server_type": "ax162",
            "cpu_cores": 48,
            "ram_gb": 256,
            "storage_gb": 8000,
            "bandwidth_tb": 20,
            "max_apps": 50,
            "description": "EPYC 9454P, enterprise scale",
            "cost": 210,
            "cost_currency": "EUR",
        },

        # ============================================
        # VULTR PLANS (For BTC templates only)
        # Hetzner ToS prohibits crypto-related services
        # ============================================

        # Cloud Servers (Vultr VC2 - Shared vCPU)
        {
            "plan_name": "starter-vultr",
            "title": "Starter",
            "category": "cloud",
            "provider": "Vultr",
            "provider_server_type": "vc2-1c-2gb",
            "cpu_cores": 1,
            "ram_gb": 2,
            "storage_gb": 55,
            "bandwidth_tb": 2,
            "max_apps": 2,
            "description": "Dev/staging, small BTC apps",
            "cost": 10,
            "cost_currency": "USD",
        },
        {
            "plan_name": "growth-vultr",
            "title": "Growth",
            "category": "cloud",
            "provider": "Vultr",
            "provider_server_type": "vc2-2c-4gb",
            "cpu_cores": 2,
            "ram_gb": 4,
            "storage_gb": 80,
            "bandwidth_tb": 3,
            "max_apps": 3,
            "description": "Small BTC production apps",
            "cost": 20,
            "cost_currency": "USD",
        },
        {
            "plan_name": "scale-vultr",
            "title": "Scale",
            "category": "cloud",
            "provider": "Vultr",
            "provider_server_type": "vc2-4c-8gb",
            "cpu_cores": 4,
            "ram_gb": 8,
            "storage_gb": 160,
            "bandwidth_tb": 4,
            "max_apps": 5,
            "description": "Multiple BTC apps",
            "cost": 40,
            "cost_currency": "USD",
        },
        # Pro Servers (Vultr VHP - High Performance)
        {
            "plan_name": "pro-vultr",
            "title": "Pro",
            "category": "pro",
            "provider": "Vultr",
            "provider_server_type": "vhp-4c-16gb-amd",
            "cpu_cores": 4,
            "ram_gb": 16,
            "storage_gb": 240,
            "bandwidth_tb": 6,
            "max_apps": 5,
            "description": "BTCPay Server, LNbits production",
            "cost": 110,
            "cost_currency": "USD",
        },
        {
            "plan_name": "business-vultr",
            "title": "Business",
            "category": "pro",
            "provider": "Vultr",
            "provider_server_type": "vhp-8c-32gb-amd",
            "cpu_cores": 8,
            "ram_gb": 32,
            "storage_gb": 480,
            "bandwidth_tb": 7,
            "max_apps": 10,
            "description": "Lightning node + BTCPay + apps",
            "cost": 220,
            "cost_currency": "USD",
        },
        {
            "plan_name": "enterprise-vultr",
            "title": "Enterprise",
            "category": "pro",
            "provider": "Vultr",
            "provider_server_type": "vhp-16c-64gb-amd",
            "cpu_cores": 16,
            "ram_gb": 64,
            "storage_gb": 960,
            "bandwidth_tb": 8,
            "max_apps": 15,
            "description": "Full Bitcoin infrastructure",
            "cost": 441,
            "cost_currency": "USD",
        },
        # Dedicated Servers (Vultr Bare Metal)
        {
            "plan_name": "metal-vultr",
            "title": "Metal",
            "category": "dedicated",
            "provider": "Vultr",
            "provider_server_type": "vbm-6c-32gb",
            "cpu_cores": 6,
            "ram_gb": 32,
            "storage_gb": 1900,
            "bandwidth_tb": 5,
            "max_apps": 15,
            "description": "Intel E-2286G, bare metal BTC node",
            "cost": 185,
            "cost_currency": "USD",
        },
        {
            "plan_name": "metal-pro-vultr",
            "title": "Metal Pro",
            "category": "dedicated",
            "provider": "Vultr",
            "provider_server_type": "vbm-8c-128gb",
            "cpu_cores": 8,
            "ram_gb": 128,
            "storage_gb": 4000,
            "bandwidth_tb": 5,
            "max_apps": 20,
            "description": "Full Bitcoin/Lightning infrastructure",
            "cost": 350,
            "cost_currency": "USD",
        },
    ]

    for plan_data in plans:
        # Calculate USD price from provider cost
        cost = plan_data.pop("cost")
        currency = plan_data.pop("cost_currency")

        if currency == "EUR":
            plan_data["price_usd"] = calc_price_eur(cost)
        else:
            plan_data["price_usd"] = calc_price_usd(cost)

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
        # ============================================
        # BTC TEMPLATES (Require Vultr - Hetzner ToS)
        # ============================================
        {
            "template_name": "btcpay",
            "title": "BTCPay Server",
            "category": "Bitcoin",
            "version": "latest",
            "min_ram_mb": 2048,
            "min_storage_gb": 50,
            "internal_port": 80,
            "healthcheck_path": "/",
            "requires_database": 1,
            "database_type": "PostgreSQL",
            "requires_vultr": 1,
            "description": "Self-hosted Bitcoin payment processor",
            "docker_compose": """version: '3'
services:
  btcpay:
    image: btcpayserver/btcpayserver:latest
    container_name: {{ container_name }}
    restart: unless-stopped
    ports:
      - "{{ port }}:80"
    environment:
      BTCPAY_POSTGRES: Host=db;Database=btcpay;Username=btcpay;Password={{ db_password }}
      BTCPAY_NETWORK: mainnet
      BTCPAY_BIND: 0.0.0.0:80
    volumes:
      - ./btcpay:/datadir
    depends_on:
      - db

  db:
    image: postgres:14
    container_name: {{ container_name }}-db
    restart: unless-stopped
    environment:
      POSTGRES_DB: btcpay
      POSTGRES_USER: btcpay
      POSTGRES_PASSWORD: {{ db_password }}
    volumes:
      - ./postgres:/var/lib/postgresql/data
""",
        },
        {
            "template_name": "lnbits",
            "title": "LNbits",
            "category": "Bitcoin",
            "version": "latest",
            "min_ram_mb": 512,
            "min_storage_gb": 5,
            "internal_port": 5000,
            "healthcheck_path": "/",
            "requires_database": 1,
            "database_type": "PostgreSQL",
            "requires_vultr": 1,
            "description": "Lightning wallet and extensions platform",
            "docker_compose": """version: '3'
services:
  lnbits:
    image: lnbits/lnbits:latest
    container_name: {{ container_name }}
    restart: unless-stopped
    ports:
      - "{{ port }}:5000"
    environment:
      LNBITS_DATABASE_URL: postgres://lnbits:{{ db_password }}@db:5432/lnbits
      LNBITS_SITE_TITLE: {{ site_title }}
    volumes:
      - ./lnbits:/app/data
    depends_on:
      - db

  db:
    image: postgres:14
    container_name: {{ container_name }}-db
    restart: unless-stopped
    environment:
      POSTGRES_DB: lnbits
      POSTGRES_USER: lnbits
      POSTGRES_PASSWORD: {{ db_password }}
    volumes:
      - ./postgres:/var/lib/postgresql/data
""",
        },
        {
            "template_name": "mempool",
            "title": "Mempool",
            "category": "Bitcoin",
            "version": "latest",
            "min_ram_mb": 4096,
            "min_storage_gb": 100,
            "internal_port": 8080,
            "healthcheck_path": "/",
            "requires_database": 1,
            "database_type": "MySQL",
            "requires_vultr": 1,
            "description": "Bitcoin blockchain explorer",
            "docker_compose": """version: '3'
services:
  web:
    image: mempool/frontend:latest
    container_name: {{ container_name }}-web
    restart: unless-stopped
    ports:
      - "{{ port }}:8080"
    environment:
      FRONTEND_HTTP_PORT: 8080
      BACKEND_MAINNET_HTTP_HOST: api
    depends_on:
      - api

  api:
    image: mempool/backend:latest
    container_name: {{ container_name }}-api
    restart: unless-stopped
    environment:
      MEMPOOL_BACKEND: electrum
      DATABASE_HOST: db
      DATABASE_DATABASE: mempool
      DATABASE_USERNAME: mempool
      DATABASE_PASSWORD: {{ db_password }}
    depends_on:
      - db

  db:
    image: mariadb:10
    container_name: {{ container_name }}-db
    restart: unless-stopped
    environment:
      MYSQL_DATABASE: mempool
      MYSQL_USER: mempool
      MYSQL_PASSWORD: {{ db_password }}
      MYSQL_ROOT_PASSWORD: {{ db_root_password }}
    volumes:
      - ./mysql:/var/lib/mysql
""",
        },
        {
            "template_name": "umbrel",
            "title": "Umbrel",
            "category": "Bitcoin",
            "version": "latest",
            "min_ram_mb": 4096,
            "min_storage_gb": 500,
            "internal_port": 80,
            "healthcheck_path": "/",
            "requires_database": 0,
            "requires_vultr": 1,
            "description": "Personal Bitcoin node with app store",
            "docker_compose": """# Umbrel requires special installation
# Use the Umbrel installer script
# curl -L https://umbrel.sh | bash
""",
        },
    ]

    for template_data in templates:
        if not frappe.db.exists("App Template", template_data["template_name"]):
            doc = frappe.get_doc({"doctype": "App Template", **template_data})
            doc.insert(ignore_permissions=True)
