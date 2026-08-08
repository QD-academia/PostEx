# Docker placeholder

Build from the repository root:

```bash
docker build -f docker/Dockerfile -t postex:dev .
docker run --rm postex:dev workflow-demo
```

The base image runs the shared core only. It does not include PowerPoint or LibreOffice and cannot produce production PDF output yet. Mount source files read-only and output separately. Pass API keys only when an approved cloud run is intentionally performed.

