
# Monitoring & Metrics

## Prometheus Integration

Burgonet Gateway provides built-in Prometheus metrics endpoint for monitoring and alerting. The metrics are exposed on the configured host and port (default: `127.0.0.1:6192`).

### Configuration

The Prometheus endpoint can be configured in `conf.yml`:

```yaml
prometheus_host: 127.0.0.1  # Host to expose metrics on
prometheus_port: 6192       # Port for metrics endpoint
```

### Available Metrics

The gateway exposes the following metrics:

- **burgonet_requests_total** (counter): Total number of requests processed
- **burgonet_input_tokens_total** (counter): Total number of input tokens processed
- **burgonet_output_tokens_total** (counter): Total number of output tokens generated

### Example Prometheus Queries

1. Requests per minute:
```promql
rate(burgonet_requests_total[1m])
```

2. Input tokens per hour:
```promql
rate(burgonet_input_tokens_total[1h])
```

3. Output tokens per day:
```promql
rate(burgonet_output_tokens_total[1d])
```

4. Token ratio (output/input):
```promql
burgonet_output_tokens_total / burgonet_input_tokens_total
```

### Grafana Dashboard

A sample Grafana dashboard is available in the `docs/grafana` directory. It includes:

- Request rate over time
- Token usage trends
- Error rates
- System resource utilization

### Alerting Examples

1. High request rate alert:
```yaml
- alert: HighRequestRate
  expr: rate(burgonet_requests_total[5m]) > 1000
  for: 10m
  labels:
    severity: critical
  annotations:
    summary: "High request rate detected"
    description: "Request rate is above 1000 req/min for 10 minutes"
```

2. Token quota warning:
```yaml
- alert: TokenQuotaWarning  
  expr: burgonet_input_tokens_total % 1000000 > 900000
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Token quota nearing limit"
    description: "Token usage is over 90% of quota"
```

### Best Practices

- Monitor request rates and token usage trends
- Set alerts for quota thresholds
- Track token ratios to detect anomalies
- Correlate metrics with system resource usage

