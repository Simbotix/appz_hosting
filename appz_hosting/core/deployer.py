"""
Deployment Engine for AppZ Hosting

Handles all deployment operations via SSH + Docker Compose.
"""

import frappe
import paramiko
import secrets
import os
from jinja2 import Template


class Deployer:
    """Handles all deployment operations via SSH"""

    def __init__(self, server_name):
        self.server = frappe.get_doc("AppZ Server", server_name)
        self.ssh = None

    def _connect(self):
        """Establish SSH connection"""
        if self.ssh:
            return self.ssh

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        key_path = self.server.ssh_key or os.path.expanduser("~/.ssh/id_rsa")
        key = paramiko.RSAKey.from_private_key_file(key_path)

        ssh.connect(
            self.server.ip_address,
            username="root",
            pkey=key,
            timeout=30
        )
        self.ssh = ssh
        return ssh

    def _exec(self, cmd, timeout=60):
        """Execute command via SSH"""
        ssh = self._connect()
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
        exit_code = stdout.channel.recv_exit_status()
        return {
            "stdout": stdout.read().decode(),
            "stderr": stderr.read().decode(),
            "exit_code": exit_code
        }

    def _upload_file(self, local_content, remote_path):
        """Upload file content to server"""
        ssh = self._connect()
        sftp = ssh.open_sftp()

        # Ensure directory exists
        remote_dir = os.path.dirname(remote_path)
        try:
            sftp.stat(remote_dir)
        except FileNotFoundError:
            self._exec(f"mkdir -p {remote_dir}")

        with sftp.file(remote_path, "w") as f:
            f.write(local_content)
        sftp.close()

    def setup_server(self):
        """Initial server setup - Docker, Caddy, network"""
        commands = [
            # Install Docker
            "curl -fsSL https://get.docker.com | sh",
            # Create Docker network
            "docker network create appz-network 2>/dev/null || true",
            # Create directories
            "mkdir -p /apps/caddy",
            # Pull Caddy image
            "docker pull caddy:2-alpine",
        ]

        for cmd in commands:
            result = self._exec(cmd, timeout=300)
            if result["exit_code"] != 0 and "already exists" not in result["stderr"]:
                frappe.log_error(f"Setup command failed: {cmd}\n{result['stderr']}")

        # Setup Caddy
        self._setup_caddy()

        return {"success": True, "message": "Server setup complete"}

    def _setup_caddy(self):
        """Setup Caddy reverse proxy"""
        compose = """version: "3.8"
services:
  caddy:
    image: caddy:2-alpine
    container_name: caddy
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
      - "443:443/udp"
    volumes:
      - /apps/caddy/Caddyfile:/etc/caddy/Caddyfile
      - /apps/caddy/data:/data
      - /apps/caddy/config:/config
    networks:
      - appz-network

networks:
  appz-network:
    external: true
"""
        self._upload_file(compose, "/apps/caddy/docker-compose.yml")
        self._upload_file("# Empty Caddyfile\n", "/apps/caddy/Caddyfile")
        self._exec("cd /apps/caddy && docker compose up -d")

    def deploy_service(self, service_name):
        """Deploy a hosted service"""
        service = frappe.get_doc("Hosted Service", service_name)
        plan = frappe.get_doc("Service Plan", service.plan)
        template = frappe.get_doc("Deployment Template", plan.template)

        # Generate credentials
        credentials = {
            "db_password": secrets.token_urlsafe(16),
            "db_root_password": secrets.token_urlsafe(16),
            "admin_password": secrets.token_urlsafe(12),
            "encryption_key": secrets.token_urlsafe(32),
        }

        # Get compose template
        compose_content = template.get_compose_content()
        if not compose_content:
            compose_content = self._get_default_compose(template.name)

        # Render template
        variables = {
            "SERVICE_ID": service.name,
            "DOMAIN": service.domain,
            "DATA_PATH": f"/apps/{service.name}",
            "DB_PASSWORD": credentials["db_password"],
            "DB_ROOT_PASSWORD": credentials["db_root_password"],
            "ADMIN_PASSWORD": credentials["admin_password"],
            "ENCRYPTION_KEY": credentials["encryption_key"],
            "RAM_LIMIT": f"{template.recommended_ram_mb}M",
            "CPU_LIMIT": str(template.min_cpu),
        }

        rendered_compose = Template(compose_content).render(**variables)

        # Create directories
        self._exec(f"mkdir -p /apps/{service.name}")

        # Upload compose file
        self._upload_file(rendered_compose, f"/apps/{service.name}/docker-compose.yml")

        # Deploy
        result = self._exec(f"cd /apps/{service.name} && docker compose up -d", timeout=300)
        if result["exit_code"] != 0:
            raise Exception(f"Deployment failed: {result['stderr']}")

        # Update Caddy
        self._update_caddy()

        return {
            "success": True,
            "compose": rendered_compose,
            "credentials": credentials
        }

    def _get_default_compose(self, template_name):
        """Get default compose file for known templates"""
        templates = {
            "wordpress": self._wordpress_compose(),
            "n8n": self._n8n_compose(),
            "ghost": self._ghost_compose(),
        }
        return templates.get(template_name, "")

    def _wordpress_compose(self):
        return '''version: "3.8"
services:
  app:
    image: wordpress:6.4-php8.2-apache
    container_name: {{ SERVICE_ID }}-app
    restart: unless-stopped
    environment:
      WORDPRESS_DB_HOST: db
      WORDPRESS_DB_NAME: wordpress
      WORDPRESS_DB_USER: wordpress
      WORDPRESS_DB_PASSWORD: {{ DB_PASSWORD }}
    volumes:
      - {{ DATA_PATH }}/wp-content:/var/www/html/wp-content
    networks:
      - internal
      - appz-network
    deploy:
      resources:
        limits:
          memory: {{ RAM_LIMIT }}

  db:
    image: mariadb:10.11
    container_name: {{ SERVICE_ID }}-db
    restart: unless-stopped
    environment:
      MYSQL_ROOT_PASSWORD: {{ DB_ROOT_PASSWORD }}
      MYSQL_DATABASE: wordpress
      MYSQL_USER: wordpress
      MYSQL_PASSWORD: {{ DB_PASSWORD }}
    volumes:
      - {{ DATA_PATH }}/mysql:/var/lib/mysql
    networks:
      - internal

networks:
  internal:
  appz-network:
    external: true
'''

    def _n8n_compose(self):
        return '''version: "3.8"
services:
  app:
    image: n8nio/n8n:latest
    container_name: {{ SERVICE_ID }}-app
    restart: unless-stopped
    environment:
      - N8N_HOST={{ DOMAIN }}
      - N8N_PORT=5678
      - N8N_PROTOCOL=https
      - WEBHOOK_URL=https://{{ DOMAIN }}/
      - N8N_ENCRYPTION_KEY={{ ENCRYPTION_KEY }}
      - DB_TYPE=postgresdb
      - DB_POSTGRESDB_HOST=db
      - DB_POSTGRESDB_DATABASE=n8n
      - DB_POSTGRESDB_USER=n8n
      - DB_POSTGRESDB_PASSWORD={{ DB_PASSWORD }}
    volumes:
      - {{ DATA_PATH }}/n8n:/home/node/.n8n
    networks:
      - internal
      - appz-network
    deploy:
      resources:
        limits:
          memory: {{ RAM_LIMIT }}

  db:
    image: postgres:15-alpine
    container_name: {{ SERVICE_ID }}-db
    restart: unless-stopped
    environment:
      POSTGRES_DB: n8n
      POSTGRES_USER: n8n
      POSTGRES_PASSWORD: {{ DB_PASSWORD }}
    volumes:
      - {{ DATA_PATH }}/postgres:/var/lib/postgresql/data
    networks:
      - internal

networks:
  internal:
  appz-network:
    external: true
'''

    def _ghost_compose(self):
        return '''version: "3.8"
services:
  app:
    image: ghost:5-alpine
    container_name: {{ SERVICE_ID }}-app
    restart: unless-stopped
    environment:
      url: https://{{ DOMAIN }}
      database__client: mysql
      database__connection__host: db
      database__connection__database: ghost
      database__connection__user: ghost
      database__connection__password: {{ DB_PASSWORD }}
    volumes:
      - {{ DATA_PATH }}/content:/var/lib/ghost/content
    networks:
      - internal
      - appz-network
    deploy:
      resources:
        limits:
          memory: {{ RAM_LIMIT }}

  db:
    image: mysql:8.0
    container_name: {{ SERVICE_ID }}-db
    restart: unless-stopped
    environment:
      MYSQL_ROOT_PASSWORD: {{ DB_ROOT_PASSWORD }}
      MYSQL_DATABASE: ghost
      MYSQL_USER: ghost
      MYSQL_PASSWORD: {{ DB_PASSWORD }}
    volumes:
      - {{ DATA_PATH }}/mysql:/var/lib/mysql
    networks:
      - internal

networks:
  internal:
  appz-network:
    external: true
'''

    def _update_caddy(self):
        """Regenerate and reload Caddyfile"""
        from appz_hosting.core.caddy import generate_caddyfile

        caddyfile = generate_caddyfile(self.server.name)
        self._upload_file(caddyfile, "/apps/caddy/Caddyfile")
        self._exec("docker exec caddy caddy reload --config /etc/caddy/Caddyfile")

    def stop_service(self, service_name):
        """Stop a service"""
        result = self._exec(f"cd /apps/{service_name} && docker compose down")
        self._update_caddy()
        return result

    def restart_service(self, service_name):
        """Restart a service"""
        return self._exec(f"cd /apps/{service_name} && docker compose restart")

    def remove_service(self, service_name):
        """Completely remove a service"""
        self._exec(f"cd /apps/{service_name} && docker compose down -v")
        self._exec(f"rm -rf /apps/{service_name}")
        self._update_caddy()

    def get_logs(self, service_name, lines=100):
        """Get service logs"""
        result = self._exec(f"cd /apps/{service_name} && docker compose logs --tail {lines}")
        return result["stdout"]

    def get_stats(self, service_name):
        """Get resource usage for a service"""
        result = self._exec(
            f"docker stats --no-stream --format '{{{{.Name}}}}|{{{{.MemUsage}}}}|{{{{.CPUPerc}}}}' "
            f"$(docker ps -q --filter name={service_name})"
        )
        return result["stdout"]

    def get_server_stats(self):
        """Get overall server stats"""
        # Memory
        mem_result = self._exec("free -g | grep Mem | awk '{print $3}'")
        used_ram_gb = float(mem_result["stdout"].strip() or 0)

        # CPU
        cpu_result = self._exec("top -bn1 | grep 'Cpu(s)' | awk '{print $2}'")
        cpu_percent = float(cpu_result["stdout"].strip().replace(",", ".") or 0)

        # Disk
        disk_result = self._exec("df -BG /apps | tail -1 | awk '{print $3}'")
        used_storage = disk_result["stdout"].strip().replace("G", "")
        used_storage_gb = float(used_storage or 0)

        return {
            "used_ram_gb": used_ram_gb,
            "used_cpu_cores": cpu_percent / 100 * self.server.total_cpu_cores,
            "used_storage_gb": used_storage_gb
        }

    def close(self):
        """Close SSH connection"""
        if self.ssh:
            self.ssh.close()
            self.ssh = None
