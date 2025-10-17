# GitHub Action Guide

MCP Testbench can be integrated into your CI/CD pipeline as a GitHub Action.

## Quick Start

Add this to `.github/workflows/security.yml`:

```yaml
name: MCP Security Scan

on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Start MCP Server
        run: |
          # Start your server here
          npm start &
          sleep 5

      - name: Security Test
        uses: ubermorgenland/mcp-testbench@v1
        with:
          target: 'http://localhost:8000'
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `target` | MCP server URL | No* | - |
| `docker-mode` | Enable Docker isolation | No | `false` |
| `docker-path` | Path to MCP server directory | No | `.` |
| `output-dir` | Output directory for reports | No | `./mcp_testbench_report` |
| `fail-on-score` | Fail if score below grade (A-F) | No | `C` |

\* Required when `docker-mode` is `false`

## Outputs

| Output | Description |
|--------|-------------|
| `security-score` | Security grade (A-F) |
| `report-path` | Path to JSON report |
| `badge-path` | Path to badge markdown |

## Usage Examples

### Basic Testing

Test a running MCP server:

```yaml
- name: Security Test
  uses: ubermorgenland/mcp-testbench@v1
  with:
    target: 'http://localhost:8000'
    fail-on-score: 'C'
```

### Docker Isolated Mode (Recommended)

For maximum security, use Docker isolation:

```yaml
- name: Security Test (Docker)
  uses: ubermorgenland/mcp-testbench@v1
  with:
    docker-mode: 'true'
    docker-path: './my-mcp-server'
    fail-on-score: 'B'
```

### Custom Output Directory

```yaml
- name: Security Test
  uses: ubermorgenland/mcp-testbench@v1
  with:
    target: 'http://localhost:8000'
    output-dir: './security-reports'
```

### Use Outputs in Subsequent Steps

```yaml
- name: Security Test
  id: security
  uses: ubermorgenland/mcp-testbench@v1
  with:
    target: 'http://localhost:8000'

- name: Display Score
  run: |
    echo "Security Score: ${{ steps.security.outputs.security-score }}"
    cat ${{ steps.security.outputs.badge-path }}
```

### Update README Badge on Push

```yaml
- name: Security Test
  id: scan
  uses: ubermorgenland/mcp-testbench@v1
  with:
    target: 'http://localhost:8000'

- name: Update README Badge
  if: github.ref == 'refs/heads/main'
  run: |
    cp ${{ steps.scan.outputs.badge-path }} ./SECURITY_BADGE.md
    git add SECURITY_BADGE.md
    git commit -m "Update security badge [skip ci]"
    git push
```

### Matrix Testing

Test multiple versions:

```yaml
strategy:
  matrix:
    node-version: [16, 18, 20]

steps:
  - uses: actions/checkout@v4

  - name: Setup Node
    uses: actions/setup-node@v4
    with:
      node-version: ${{ matrix.node-version }}

  - name: Start Server
    run: npm start &

  - name: Security Test
    uses: ubermorgenland/mcp-testbench@v1
    with:
      target: 'http://localhost:8000'
      output-dir: './reports-node-${{ matrix.node-version }}'
```

### Scheduled Daily Scans

```yaml
on:
  schedule:
    - cron: '0 2 * * *'  # 2 AM UTC daily

jobs:
  daily-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Security Test
        uses: ubermorgenland/mcp-testbench@v1
        with:
          target: 'http://localhost:8000'
          fail-on-score: 'D'

      - name: Create Issue on Failure
        if: failure()
        uses: actions/github-script@v7
        with:
          script: |
            github.rest.issues.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              title: '🚨 Security Scan Failed',
              body: 'Daily security scan detected vulnerabilities.',
              labels: ['security']
            });
```

## Security Score Thresholds

Configure `fail-on-score` based on your risk tolerance:

| Grade | Recommended For | Description |
|-------|----------------|-------------|
| `A` | Production, Public APIs | Zero vulnerabilities |
| `B` | Staging, Internal Tools | Minor issues acceptable |
| `C` | Development, Testing | Moderate risk tolerance |
| `D` | Early Development | High risk tolerance |
| `F` | Never Recommended | Critical vulnerabilities |

## Artifacts

The action automatically uploads security reports as artifacts:

```yaml
# Reports are available for 30 days
- name: Download Reports
  uses: actions/download-artifact@v4
  with:
    name: mcp-security-report
```

## PR Comments

On pull requests, the action automatically comments with results:

```
🛡️ MCP Security Scan Results

![MCP Security Score](https://img.shields.io/badge/Security-B-green)

Security Score: B
```

## Troubleshooting

### Action fails with "target required"

**Solution**: Provide `target` when not using Docker mode:

```yaml
with:
  target: 'http://localhost:8000'
```

### Docker mode not finding server

**Solution**: Ensure `docker-path` points to your MCP server directory:

```yaml
with:
  docker-mode: 'true'
  docker-path: './path/to/server'
```

### Health check timeout

**Solution**: Your server may take longer to start. Add a wait step:

```yaml
- name: Start Server
  run: |
    npm start &
    sleep 10  # Increase wait time
```

### Permission denied

**Solution**: Ensure Docker daemon is accessible (for Docker mode):

```yaml
- name: Set up Docker
  uses: docker/setup-buildx-action@v3
```

## Advanced Configuration

### Custom Test Selection

Currently tests all plugins. Plugin selection coming in v2.

### Integration with Other Security Tools

Combine with other security scanners:

```yaml
- name: npm audit
  run: npm audit

- name: MCP Security
  uses: ubermorgenland/mcp-testbench@v1
  with:
    target: 'http://localhost:8000'

- name: OWASP ZAP
  uses: zaproxy/action-baseline@v0.7.0
```

## Examples

See `.github/workflows/` for complete examples:
- `example-basic.yml` - Simple direct testing
- `example-docker.yml` - Docker isolated mode
- `example-scheduled.yml` - Daily scheduled scans

## Support

- [Documentation](https://github.com/ubermorgenland/mcp-testbench)
- [Report Issues](https://github.com/ubermorgenland/mcp-testbench/issues)
- [Twitter](https://twitter.com/ApInference)
