# GitHub Configuration

This directory contains GitHub-specific configurations used for project automation and collaboration.

## Structure

```
.github/
├── workflows/
│   ├── ci.yml
│   ├── tests.yml
│   ├── lint.yml
│   ├── docker.yml
│   └── release.yml
```

## Purpose

- Continuous Integration (CI)
- Automated Testing
- Code Quality Checks
- Docker Image Builds
- Release Automation

## Workflows

| Workflow | Description |
|-----------|-------------|
| ci.yml | Main CI pipeline |
| tests.yml | Execute automated tests |
| lint.yml | Run formatting and linting |
| docker.yml | Build Docker images |
| release.yml | Create GitHub Releases |

These workflows are executed automatically on GitHub Actions.