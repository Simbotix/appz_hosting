"""
Server Provisioner - Provisions servers via Hetzner/Vultr API
"""

import frappe
import requests


def provision_server(server_name):
    """Provision a new server"""
    server = frappe.get_doc("Customer Server", server_name)
    plan = frappe.get_doc("Server Plan", server.plan)

    try:
        if server.provider == "Hetzner":
            result = provision_hetzner(server, plan)
        elif server.provider == "Vultr":
            result = provision_vultr(server, plan)
        else:
            raise ValueError(f"Unknown provider: {server.provider}")

        if result.get("success"):
            server.ip_address = result.get("ip_address")
            server.provider_server_id = result.get("server_id")
            server.status = "Active"
            server.save(ignore_permissions=True)

            # Run bootstrap script
            frappe.enqueue(
                "appz_hosting.core.provisioner.bootstrap_server",
                server_name=server.name,
            )

        return result

    except Exception as e:
        frappe.log_error(f"Provisioning failed for {server_name}: {e}")
        server.status = "Error"
        server.notes = str(e)
        server.save(ignore_permissions=True)
        return {"success": False, "error": str(e)}


def provision_hetzner(server, plan):
    """Provision server on Hetzner"""
    api_key = frappe.conf.get("hetzner_api_key")
    if not api_key:
        raise ValueError("Hetzner API key not configured")

    # Create server via Hetzner API
    response = requests.post(
        "https://api.hetzner.cloud/v1/servers",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "name": f"appz-{server.name.lower()}",
            "server_type": plan.provider_server_type or "cx32",
            "image": "ubuntu-22.04",
            "location": "fsn1",
            "ssh_keys": frappe.conf.get("hetzner_ssh_keys", []),
        },
    )

    if response.status_code == 201:
        data = response.json()
        return {
            "success": True,
            "server_id": str(data["server"]["id"]),
            "ip_address": data["server"]["public_net"]["ipv4"]["ip"],
        }
    else:
        return {"success": False, "error": response.text}


def provision_vultr(server, plan):
    """Provision server on Vultr"""
    api_key = frappe.conf.get("vultr_api_key")
    if not api_key:
        raise ValueError("Vultr API key not configured")

    # Create server via Vultr API
    response = requests.post(
        "https://api.vultr.com/v2/instances",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "label": f"appz-{server.name.lower()}",
            "plan": plan.provider_server_type or "vc2-1c-1gb",
            "os_id": 1743,  # Ubuntu 22.04
            "region": "fra",
        },
    )

    if response.status_code == 202:
        data = response.json()
        return {
            "success": True,
            "server_id": data["instance"]["id"],
            "ip_address": data["instance"]["main_ip"],
        }
    else:
        return {"success": False, "error": response.text}


def bootstrap_server(server_name):
    """Bootstrap a newly provisioned server with Docker, Caddy, etc."""
    server = frappe.get_doc("Customer Server", server_name)

    from appz_hosting.core.deployer import Deployer

    try:
        deployer = Deployer(server_name)

        # Install Docker
        deployer._exec(
            """
            curl -fsSL https://get.docker.com | sh
            systemctl enable docker
            systemctl start docker
        """,
            timeout=300,
        )

        # Install Caddy
        deployer._exec(
            """
            apt-get update
            apt-get install -y debian-keyring debian-archive-keyring apt-transport-https
            curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
            curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list
            apt-get update
            apt-get install -y caddy
        """,
            timeout=300,
        )

        # Create app directory
        deployer._exec("mkdir -p /apps")

        deployer.close()

        frappe.logger().info(f"Bootstrap complete for {server_name}")

    except Exception as e:
        frappe.log_error(f"Bootstrap failed for {server_name}: {e}")


def destroy_server(server):
    """Destroy a server"""
    try:
        if server.provider == "Hetzner":
            return destroy_hetzner(server)
        elif server.provider == "Vultr":
            return destroy_vultr(server)
    except Exception as e:
        return {"success": False, "error": str(e)}


def destroy_hetzner(server):
    """Destroy Hetzner server"""
    api_key = frappe.conf.get("hetzner_api_key")
    response = requests.delete(
        f"https://api.hetzner.cloud/v1/servers/{server.provider_server_id}",
        headers={"Authorization": f"Bearer {api_key}"},
    )
    return {"success": response.status_code == 200}


def destroy_vultr(server):
    """Destroy Vultr server"""
    api_key = frappe.conf.get("vultr_api_key")
    response = requests.delete(
        f"https://api.vultr.com/v2/instances/{server.provider_server_id}",
        headers={"Authorization": f"Bearer {api_key}"},
    )
    return {"success": response.status_code == 204}
