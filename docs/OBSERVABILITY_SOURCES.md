# External references for observability and deployment

These sources were consulted before implementing the monitoring and deployment changes.

## Grafana Alloy

Grafana states that Promtail reached end of life on March 2, 2026 and that future feature development belongs in Grafana Alloy: https://grafana.com/docs/loki/latest/send-data/promtail/

Grafana Alloy documentation describes `loki.source.docker` for reading log entries from Docker containers through the Docker daemon and forwarding them to Loki. The official Docker monitoring example uses `discovery.docker`, `discovery.relabel`, `loki.source.docker`, `loki.write`, `prometheus.exporter.cadvisor`, and `prometheus.scrape`: https://grafana.com/docs/alloy/latest/reference/components/loki/loki.source.docker/ and https://grafana.com/docs/alloy/latest/monitor/monitor-docker-containers/

The recommended local topology is Alloy with read-only Docker socket access, Loki for log storage, Prometheus for metrics, cAdvisor for container metrics, and Grafana for dashboards and Explore views.

## GitHub Actions secrets

GitHub's official documentation states that repository, environment, and organization secrets are managed separately; workflows access them through the `secrets` context. It also recommends masking sensitive values and avoiding passing secrets on command lines when possible: https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions

## Docker Compose environment handling

Docker's official Compose documentation explains the `environment` and `env_file` mechanisms and their precedence. Sensitive values should not be committed to Compose files or `.env.example`: https://docs.docker.com/compose/how-tos/environment-variables/set-environment-variables/
