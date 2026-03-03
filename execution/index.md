# Oracy AI - Execution Guide

## Overview

This directory contains executable instructions for setting up, running, and deploying the Oracy AI platform. These guides bridge the gap between planning documentation and actual implementation.

## Quick Start

```bash
# 1. Clone and setup
git clone <repository-url>
cd oracy

# 2. Run setup (see 01-setup-and-installation.md)
# 3. Configure environment (see 02-environment-configuration.md)
# 4. Start development (see 03-running-locally.md)
```

## Execution Documents

| Document | Purpose | When to Use |
|----------|---------|-------------|
| [01-setup-and-installation.md](./01-setup-and-installation.md) | Initial project setup, dependencies, tools | First-time setup or onboarding |
| [02-environment-configuration.md](./02-environment-configuration.md) | Environment variables, secrets, AWS config | Setting up new environment |
| [03-running-locally.md](./03-running-locally.md) | Local development workflow | Daily development |
| [04-database-migrations.md](./04-database-migrations.md) | Database schema changes | Modifying models |
| [05-ai-pipeline-execution.md](./05-ai-pipeline-execution.md) | Running AI pipeline stages | Testing/development of AI features |
| [06-testing-procedures.md](./06-testing-procedures.md) | Test execution procedures | Before commits, CI/CD |
| [07-deployment-execution.md](./07-deployment-execution.md) | Deploy to staging/production | Release time |
| [08-troubleshooting.md](./08-troubleshooting.md) | Common issues and fixes | When things break |

## Prerequisites

- **OS**: Windows 11, macOS 13+, or Linux (Ubuntu 22.04+)
- **Docker Desktop**: 4.25+ with WSL2 backend (Windows)
- **Node.js**: 20.x LTS
- **Python**: 3.12+
- **uv**: Modern Python package manager
- **AWS CLI**: 2.x configured with credentials
- **Git**: 2.40+

## Project Structure

```
oracy/
├── client/           # React frontend
├── server/           # Django backend
├── llm/              # AI/ML pipeline services
├── planning/         # Architecture & planning docs
├── execution/        # This directory - how-to guides
└── project-docs/     # Requirements & specifications
```

## Environment Types

| Environment | Purpose | URL |
|-------------|---------|-----|
| Local | Development | http://localhost:5173 (frontend), http://localhost:8000 (backend) |
| Staging | Pre-production testing | https://staging.oracy.ai |
| Production | Live system | https://app.oracy.ai |

## Getting Help

1. Check [08-troubleshooting.md](./08-troubleshooting.md)
2. Review planning docs in `/planning/`
3. Check project requirements in `/project-docs/`
4. File an issue with logs and reproduction steps

---

**Note**: These guides assume you're working from the project root directory (`c:/Users/rian/Documents/freelances/oracy` or equivalent).