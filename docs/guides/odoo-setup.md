# Odoo ERP Setup Guide

**Docker-based Odoo Integration for Accounting**

This guide covers complete Odoo ERP setup using Docker for business accounting integration.

---

## 📋 What You'll Set Up

- ✅ Odoo 19.0 Community Edition (Docker)
- ✅ PostgreSQL database
- ✅ Accounting/Invoicing modules
- ✅ API integration for AI Employee

---

## 🚀 Step-by-Step Setup

### Step 1: Install Docker

1. **Download Docker Desktop:**
   - [Windows](https://www.docker.com/products/docker-desktop/)
   - [Mac](https://www.docker.com/products/docker-desktop/)
   - [Linux](https://docs.docker.com/engine/install/)

2. **Install and start Docker**
3. **Verify installation:**
   ```bash
   docker --version
   docker-compose --version
   ```

### Step 2: Configure Environment Variables

Create or edit `.env` in project root:

```bash
# Odoo Configuration
ODOO_ADMIN_PASSWORD=your_secure_admin_password
ODOO_DB_PASSWORD=your_secure_db_password
```

**⚠️ Security Warning:** Change default passwords before production use!

### Step 3: Start Odoo Containers

```bash
# Navigate to project directory
cd C:\Users\Faraz\Desktop\Personal-Ai-Employe-Hackathon-0-FTE

# Start Odoo and PostgreSQL
docker-compose up -d odoo db

# Check status
docker-compose ps
```

**Expected output:**
```
NAME                    STATUS         PORTS
ai_employee_odoo        Up (healthy)   0.0.0.0:8069->8069/tcp
ai_employee_odoo_db     Up (healthy)   5432/tcp
```

### Step 4: Create Odoo Database

1. **Open browser:** http://localhost:8069
2. **Click "Create Database"**
3. **Fill in:**
   - Master Password: (from `.env`)
   - Database Name: `ai_employee`
   - Email: your email
   - Password: your admin password
   - Language: English (US)
   - Country: Your country
   - Demo Data: ✅ Check for testing
4. **Click "Create Database"**

### Step 5: Install Accounting Modules

1. **Go to Apps** (main menu)
2. **Search and install:**
   - ✅ **Invoicing** (free accounting)
   - ✅ **Contacts** (customer management)
   - ✅ **Products** (product catalog)

### Step 6: Activate Developer Mode

1. **Go to Settings**
2. **Scroll to bottom**
3. **Click "Activate the developer mode"**

### Step 7: Create API User

1. **Go to Settings → Users & Companies → Users**
2. **Click "Create"**
3. **Fill in:**
   - **Name:** AI Employee
   - **Email:** ai-employee@localhost
   - **Password:** generate secure password
4. **Set Access Rights:**
   - **Invoicing / User** ✅
   - **Contacts / User** ✅
5. **Click "Save"**

### Step 8: Generate API Key

1. **Click your profile** (top right)
2. **Click "Preferences"**
3. **Click "Generate API Key"**
4. **Save this key** - you'll need it

### Step 9: Configure .env for Odoo

Add to your `.env` file:

```bash
# Odoo Configuration
ODOO_URL=http://localhost:8069
ODOO_DB=ai_employee
ODOO_USERNAME=ai-employee@localhost
ODOO_PASSWORD=your_api_key_or_password
```

### Step 10: Test Odoo Connection

```bash
# Test connection
python scripts/odoo_connector.py --test-connection
```

**Expected output:**
```
✅ Connected to Odoo 19.0
✅ Database: ai_employee
✅ User: AI Employee
✅ Available models: account.move, res.partner, product.template, ...
```

---

## 📝 Usage Examples

### Create Invoice

```bash
# Create test invoice
python scripts/odoo_connector.py \
  --create-invoice \
  --customer "Test Customer" \
  --amount 100.00 \
  --description "Consulting Services"

# Create actual invoice for existing customer
python scripts/odoo_connector.py \
  --create-invoice \
  --customer "Client A" \
  --amount 500.00 \
  --description "January 2026 Services"
```

### Sync Invoices to Vault

```bash
# Sync all invoices
python scripts/odoo_connector.py --sync-invoices

# Sync last 30 days
python scripts/odoo_connector.py --sync-invoices --last-days 30
```

**Check:** `AI_Employee_Vault/Accounting/` folder for synced invoices

### List Customers

```bash
# List all customers
python scripts/odoo_connector.py --list-customers

# Get specific customer
python scripts/odoo_connector.py --get-customer "Client A"
```

### Register Payment

```bash
# Register payment for invoice
python scripts/odoo_connector.py \
  --register-payment \
  --invoice-id 123 \
  --amount 500.00
```

---

## 🔧 Docker Commands Reference

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart services
docker-compose restart odoo

# View logs
docker-compose logs -f odoo
docker-compose logs -f db

# Access Odoo container shell
docker exec -it ai_employee_odoo bash

# Access database shell
docker exec -it ai_employee_odoo_db psql -U odoo -d postgres

# Backup database
docker exec ai_employee_odoo_db pg_dump -U odoo postgres > backup_$(date +%Y%m%d).sql

# Restore database
docker exec -i ai_employee_odoo_db psql -U odoo postgres < backup_20260307.sql

# Remove all data (WARNING: destructive!)
docker-compose down -v
```

---

## 📊 Data Persistence

All data is stored in Docker volumes:

| Volume | Purpose | Location |
|--------|---------|----------|
| `odoo-data` | Odoo files, addons, sessions | `/var/lib/odoo` |
| `postgres-data` | Database files | `/var/lib/postgresql/data` |

**Backup Strategy:**
```bash
# Backup database daily
docker exec ai_employee_odoo_db pg_dump -U odoo postgres > backups/db-$(date +%Y%m%d).sql

# Backup Odoo files weekly
docker-compose run --rm odoo tar czf /tmp/odoo-backup.tar.gz /var/lib/odoo
docker cp ai_employee_odoo:/tmp/odoo-backup.tar.gz ./backups/
```

---

## 🛡️ Security Best Practices

1. **Change Default Passwords:**
   - Odoo admin password
   - Database password
   - API user password

2. **Use Environment Variables:**
   - Never hardcode credentials
   - Use `.env` file (add to `.gitignore`)

3. **Network Isolation:**
   - Odoo network isolates containers
   - Only expose necessary ports

4. **Regular Updates:**
   - Update Odoo image monthly
   - Update PostgreSQL image
   - Monitor security advisories

5. **Backup Strategy:**
   - Daily database backups
   - Weekly full backups
   - Test restore procedures monthly

---

## 🐛 Troubleshooting

### Odoo Won't Start

```bash
# Check logs
docker-compose logs odoo

# Common issues:
# 1. Port 8069 already in use
netstat -ano | findstr :8069

# 2. Database connection failed
docker-compose logs db

# 3. Volume permissions
docker volume prune  # WARNING: removes unused volumes
```

### Database Connection Issues

```bash
# Test database connection
docker exec -it ai_employee_odoo_db psql -U odoo -d postgres

# Reset database password
docker exec -it ai_employee_odoo_db psql -U odoo -c "ALTER USER odoo WITH PASSWORD 'newpassword';"
```

### Odoo is Slow

```bash
# Increase workers in odoo.conf
workers = 4  # For 2+ CPU cores

# Restart Odoo
docker-compose restart odoo
```

### Connection Refused

```bash
# Check if Odoo is running
docker-compose ps

# Restart if needed
docker-compose restart odoo

# Check firewall
# Ensure port 8069 is not blocked
```

---

## 📚 Resources

- [Odoo 19 Documentation](https://www.odoo.com/documentation/19.0/)
- [Odoo External API Reference](https://www.odoo.com/documentation/19.0/developer/reference/external_api.html)
- [Docker Compose Reference](https://docs.docker.com/compose/)

---

*Odoo ERP Setup Guide - Personal AI Employee*
