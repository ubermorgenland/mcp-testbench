# MCP Testbench Documentation

This directory contains the documentation for MCP Testbench.

## Publishing to docs.apinference.com

### Option 1: GitHub Pages (Recommended)

The simplest approach is to use GitHub Pages with Jekyll or a static site generator:

1. **Enable GitHub Pages** on the repository
2. **Point to `/docs` folder** in settings
3. **Add CNAME file** with `docs.apinference.com`
4. **Configure DNS** at your registrar:
   ```
   CNAME docs.apinference.com → ubermorgenland.github.io
   ```

GitHub automatically rebuilds when you push to the `docs/` folder.

### Option 2: Netlify/Vercel

1. Connect repository to Netlify/Vercel
2. Set build directory to `/docs`
3. Add custom domain: `docs.apinference.com`
4. Configure DNS:
   ```
   CNAME docs.apinference.com → [netlify/vercel URL]
   ```

### Option 3: Direct Sync

Use a GitHub Action to sync `/docs` to your server:

```yaml
name: Deploy Docs
on:
  push:
    branches: [main]
    paths: ['docs/**']

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to Server
        run: |
          rsync -avz docs/ user@apinference.com:/var/www/docs/
```

## Documentation Structure

```
docs/
├── index.md                    # Homepage
├── installation.md             # Installation guide
├── quickstart.md               # Quick start tutorial
├── cli-reference.md            # CLI commands
├── testing-stdio.md            # Stdio testing guide
├── testing-http.md             # HTTP testing guide
├── understanding-results.md    # How to read results
├── crash-analysis.md           # Real crash examples
├── github-actions.md           # CI/CD integration
├── docker-mode.md              # Docker isolation
├── plugin-development.md       # Custom plugins
└── scoring.md                  # Security scoring system
```

## Markdown Rendering

All `.md` files are written in standard Markdown and can be rendered by:
- GitHub Pages (Jekyll)
- Netlify/Vercel
- MkDocs
- Docusaurus
- Any static site generator

## Adding New Documentation

1. Create new `.md` file in `/docs`
2. Add link to `index.md` navigation
3. Commit and push
4. Documentation auto-publishes

## Local Preview

```bash
# Using Python simple server
cd docs
python -m http.server 8000

# Or using Jekyll (if installed)
jekyll serve

# Or using MkDocs (if installed)
mkdocs serve
```

---

**Maintained by**: Ubermorgen Ltd
**Product**: ApInference
**Repository**: https://github.com/ubermorgenland/mcp-testbench
