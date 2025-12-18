# AppZ Hosting

White-label Managed Hosting Platform for AppZ Studio.

## Features

- **Template Library**: Pre-tested Docker Compose templates for WordPress, n8n, Ghost, and more
- **AI Capacity Advisor**: Intelligent server capacity planning
- **Automated Backups**: Daily backups to S3-compatible storage
- **ClickStack Integration**: Optional observability addon for customers
- **Customer Portal**: Self-service dashboard for customers
- **Multi-Currency Billing**: USD, INR, BTC via ERPNext integration

## Installation

```bash
bench get-app https://github.com/Simbotix/appz_hosting
bench --site your-site install-app appz_hosting
```

## DocTypes

- **AppZ Server**: Server registry with capacity tracking
- **Deployment Template**: Tested docker-compose templates
- **Service Plan**: Customer-facing pricing plans
- **Hosted Service**: Customer service instances
- **Service Backup Config**: Backup configuration per service
- **Service Backup**: Individual backup records
- **Service Observability**: ClickStack integration settings

## Configuration

Add to your `site_config.json`:

```json
{
    "hetzner_s3_endpoint": "https://fsn1.your-objectstorage.com",
    "hetzner_s3_access_key": "your-access-key",
    "hetzner_s3_secret_key": "your-secret-key",
    "hetzner_s3_bucket": "appz-backups",
    "clickstack_endpoint": "https://otel.appz.studio"
}
```

## License

MIT
