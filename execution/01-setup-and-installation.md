# Setup and Installation

Complete guide for setting up the Oracy AI development environment from scratch.

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Install Core Dependencies](#install-core-dependencies)
3. [Clone and Initialize Project](#clone-and-initialize-project)
4. [Backend Setup](#backend-setup)
5. [Frontend Setup](#frontend-setup)
6. [Docker Setup](#docker-setup)
7. [Verify Installation](#verify-installation)

---

## System Requirements

### Hardware

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| RAM | 8 GB | 16 GB |
| Storage | 20 GB free | 50 GB free (SSD) |
| CPU | 4 cores | 8 cores |

### Operating System

- **Windows**: Windows 11 Pro/Enterprise with WSL2
- **macOS**: macOS 13 (Ventura) or later
- **Linux**: Ubuntu 22.04 LTS or equivalent

---

## Install Core Dependencies

### 1. Install Docker Desktop

**Windows:**
```powershell
# Download from https://www.docker.com/products/docker-desktop
# Or using winget
winget install Docker.DockerDesktop
```

**macOS:**
```bash
# Using Homebrew
brew install --cask docker

# Or download from https://www.docker.com/products/docker-desktop
```

**Linux (Ubuntu):**
```bash
# Add Docker's official GPG key
sudo apt-get update
sudo apt-get install ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Add repository
echo "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

### 2. Install Node.js 20.x

**Windows:**
```powershell
# Using nvm-windows or download from nodejs.org
# Or using winget
winget install OpenJS.NodeJS.LTS

# Verify
node --version  # Should show v20.x.x
npm --version
```

**macOS:**
```bash
# Using Homebrew
brew install node@20

# Verify
node --version
npm --version
```

**Linux:**
```bash
# Using NodeSource
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Verify
node --version
npm --version
```

### 3. Install Python 3.12

**Windows:**
```powershell
# Using winget
winget install Python.Python.3.12

# Or download from python.org
# IMPORTANT: Check "Add Python to PATH" during installation

# Verify
python --version  # Python 3.12.x
```

**macOS:**
```bash
# Using Homebrew
brew install python@3.12

# Add to PATH
echo 'export PATH="/opt/homebrew/opt/python@3.12/libexec/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# Verify
python3 --version
```

**Linux:**
```bash
# Using deadsnakes PPA
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.12 python3.12-venv python3.12-dev

# Verify
python3.12 --version
```

### 4. Install uv (Python Package Manager)

**All Platforms:**
```bash
# Using the official installer
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or on Windows PowerShell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Add to PATH (if not automatically added)
# Windows: Already in PATH
# macOS/Linux:
echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc  # or ~/.zshrc
source ~/.bashrc

# Verify
uv --version
```

### 5. Install AWS CLI

**Windows:**
```powershell
winget install Amazon.AWSCLI
```

**macOS:**
```bash
brew install awscli
```

**Linux:**
```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

**Verify and Configure:**
```bash
aws --version
aws configure  # Enter your AWS credentials
```

---

## Clone and Initialize Project

```bash
# Clone the repository
git clone <repository-url> oracy
cd oracy

# Verify project structure
ls -la
# Should show: client/, server/, llm/, planning/, execution/, project-docs/
```

---

## Backend Setup

### 1. Navigate to Server Directory

```bash
cd server
```

### 2. Create Virtual Environment with uv

```bash
# Create virtual environment
uv venv .venv

# Activate (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Activate (Windows CMD)
.venv\Scripts\activate.bat

# Activate (macOS/Linux)
source .venv/bin/activate

# Verify (should show path to .venv)
which python
```

### 3. Install Dependencies

```bash
# Install all dependencies including dev
uv pip install -e ".[dev]"

# Verify installation
python -c "import django; print(django.VERSION)"
python -c "import djangorestframework; print('DRF installed')"
```

### 4. Create Local Settings File

```bash
# Create development settings
copy config\settings\development.py.example config\settings\development.py

# Or on macOS/Linux
cp config/settings/development.py.example config/settings/development.py
```

Edit `config/settings/development.py` with local database credentials.

### 5. Verify Backend Setup

```bash
# Check Django commands work
python manage.py help

# Should list available commands without errors
```

---

## Frontend Setup

### 1. Navigate to Client Directory

```bash
cd ../client
# or from root: cd client
```

### 2. Install Dependencies

```bash
# Using npm
npm install

# Or using pnpm (faster)
pnpm install

# This will install all packages from package.json
```

### 3. Verify Frontend Setup

```bash
# Check package installation
npm list react
npm list vite

# Should show versions without errors
```

---

## Docker Setup

### 1. Create Docker Network

```bash
# From project root
docker network create oracy-network
```

### 2. Create Docker Compose Override (Optional)

Create `docker-compose.override.yml` in project root for local customizations:

```yaml
version: '3.8'

services:
  db:
    ports:
      - "5432:5432"  # Expose PostgreSQL locally
  
  redis:
    ports:
      - "6379:6379"  # Expose Redis locally
```

### 3. Build Images

```bash
# Build all services
docker compose build

# Or build specific service
docker compose build backend
docker compose build frontend
```

---

## Verify Installation

### Run Verification Script

From project root, run:

```bash
# Windows PowerShell
.\scripts\verify-setup.ps1

# macOS/Linux
./scripts/verify-setup.sh
```

### Manual Verification Checklist

| Component | Verification Command | Expected Result |
|-----------|---------------------|-----------------|
| Docker | `docker ps` | No error, shows headers |
| Node.js | `node --version` | v20.x.x |
| Python | `python --version` | 3.12.x |
| uv | `uv --version` | Version displayed |
| AWS CLI | `aws --version` | aws-cli/2.x.x |
| Backend deps | `cd server && python -c "import django"` | No error |
| Frontend deps | `cd client && npm list react` | Shows version |

### Start Development Environment

```bash
# Using Docker Compose (recommended)
docker compose up -d

# Or start services individually
# Terminal 1 - Database & Redis
docker compose up -d db redis

# Terminal 2 - Backend
cd server
python manage.py runserver

# Terminal 3 - Frontend
cd client
npm run dev
```

### Access Points

| Service | URL | Credentials |
|---------|-----|-------------|
| Frontend | http://localhost:5173 | - |
| Backend API | http://localhost:8000 | - |
| Django Admin | http://localhost:8000/admin | Create superuser |
| API Docs | http://localhost:8000/api/docs | - |
| PostgreSQL | localhost:5432 | oracy/oracy_dev |
| Redis | localhost:6379 | - |

---

## Next Steps

1. **Configure Environment Variables**: See [02-environment-configuration.md](./02-environment-configuration.md)
2. **Run Database Migrations**: See [04-database-migrations.md](./04-database-migrations.md)
3. **Start Development**: See [03-running-locally.md](./03-running-locally.md)

---

## Troubleshooting Setup Issues

### Port Conflicts

```bash
# Check what's using port 8000
# Windows
netstat -ano | findstr :8000

# macOS/Linux
lsof -i :8000

# Kill process or change ports in docker-compose.yml
```

### Permission Denied (Linux/macOS)

```bash
# Fix permissions
sudo chown -R $USER:$USER .

# Or for Docker socket
sudo usermod -aG docker $USER
# Logout and login again
```

### Python Module Not Found

```bash
# Ensure virtual environment is activated
which python

# Reinstall dependencies
uv pip install -e ".[dev]" --force-reinstall
```

### Node Modules Issues

```bash
cd client
rm -rf node_modules package-lock.json
npm install