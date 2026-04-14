# Odoo Connector Skill

**Version:** 1.0.0  
**Type:** Gold Tier  
**Domain:** Accounting & ERP Integration

---

## 📋 Overview

This skill enables the AI Employee to interact with Odoo ERP for accounting operations including:
- Creating and managing invoices
- Customer/vendor management
- Payment registration
- Financial data synchronization

---

## 🎯 Capabilities

### 1. Invoice Management
- Create customer invoices
- Retrieve invoice history
- Sync invoices to local vault
- Track payment status

### 2. Customer Management
- List all customers
- Search customers by name/email
- Create new customers (via invoice creation)

### 3. Payment Operations
- Register payments against invoices
- Track payment status
- Payment reconciliation

---

## 🔧 Configuration

### Environment Variables

Add to your `.env` file:

```bash
# Odoo Configuration
ODOO_URL=http://localhost:8069
ODOO_DB=ai_employee
ODOO_USERNAME=ai-employee@localhost
ODOO_PASSWORD=your_secure_password
ODOO_API_KEY=your_api_key_if_applicable
```

### Docker Setup

Ensure Odoo is running via Docker Compose:

```bash
docker-compose up -d odoo db
```

---

## 📖 Usage Examples

### Test Connection

```markdown
Test the Odoo connection to ensure everything is configured correctly.
```

**Expected Output:**
```
✅ Connected to Odoo 19.0
✅ Database: ai_employee
✅ User: AI Employee
```

---

### Create Invoice

```markdown
Create an invoice for Customer A for $500 for "Consulting Services - January 2026".
Customer email: customer@example.com
Due date: 2026-04-01
```

**Expected Output:**
```
✅ Invoice created: INV/2026/00001
   Customer: Customer A
   Amount: $500.00
   Status: Draft
```

---

### Sync Invoices

```markdown
Sync all invoices from the last 30 days from Odoo to the local vault.
```

**Expected Output:**
```
✅ Synced 15 invoices to AI_Employee_Vault/Accounting/odoo_invoices_2026-03-02.md
```

---

### List Customers

```markdown
List all customers from Odoo.
```

**Expected Output:**
```
Found 25 customers:

  - Customer A (customer@example.com)
  - Customer B (contact@company.com)
  - ...
```

---

### Get Customer Details

```markdown
Find customer details for "Customer A" or customer@example.com.
```

**Expected Output:**
```
Customer found:
  Name: Customer A
  Email: customer@example.com
  Phone: +1-555-0123
  City: New York
```

---

## 🔄 Workflow Integration

### Invoice Creation Workflow

```
1. Receive request (email/WhatsApp/message)
2. Extract customer info and amount
3. Check Company Handbook for approval rules
4. If amount > threshold → Create approval request
5. If approved → Create invoice in Odoo
6. Log action to audit logs
7. Move to Done folder
```

### Approval Threshold Example

```markdown
## Company Handbook Rules

- Invoices < $100: Auto-approve
- Invoices $100-$500: Require approval for new customers
- Invoices > $500: Always require approval
```

---

## 📁 File Structure

```
AI_Employee_Vault/
├── Accounting/
│   ├── odoo_invoices_2026-03-02.md    # Synced invoices
│   └── customers.md                    # Customer list
├── Pending_Approval/
│   └── INVOICE_CustomerA_500.md       # Approval requests
├── Approved/
│   └── INVOICE_CustomerA_500.md       # Approved invoices
└── Logs/
    └── odoo_2026-03-02.log            # Odoo operations log
```

---

## 🛡️ Security & Approval

### When to Request Approval

| Scenario | Action |
|----------|--------|
| New customer, any amount | ✅ Request approval |
| Existing customer, < $100 | ✅ Auto-approve |
| Existing customer, $100-$500 | ⚠️ Use judgment |
| Any invoice, > $500 | ✅ Request approval |
| Payment registration | ✅ Always approve |

### Approval File Template

```markdown
---
type: approval_request
action: create_invoice
customer: Customer A
amount: 500.00
description: Consulting Services - January 2026
created: 2026-03-02T10:30:00Z
status: pending
---

## Invoice Details
- Customer: Customer A (customer@example.com)
- Amount: $500.00
- Description: Consulting Services - January 2026
- Due Date: 2026-04-01

## To Approve
Move this file to /Approved folder.

## To Reject
Move this file to /Rejected folder.
```

---

## 🐛 Error Handling

### Common Errors

#### Connection Failed
```
❌ Cannot reach Odoo server: Connection refused
```

**Solution:**
```bash
docker-compose ps  # Check if Odoo is running
docker-compose up -d  # Start Odoo
```

#### Authentication Failed
```
❌ Authentication failed
```

**Solution:**
- Verify credentials in `.env`
- Check API key validity
- Ensure user has proper permissions

#### Customer Not Found
```
Customer not found
```

**Solution:**
- Customer will be created automatically during invoice creation
- Or create customer first via Odoo UI

---

## 📊 Logging

All Odoo operations are logged to:
```
Logs/odoo_YYYY-MM-DD.log
```

**Log Entry Example:**
```json
{
  "timestamp": "2026-03-02T10:30:00Z",
  "action": "create_invoice",
  "customer": "Customer A",
  "amount": 500.00,
  "invoice_id": 123,
  "status": "success",
  "dry_run": false
}
```

---

## 🧪 Testing

### Test Commands

```bash
# Test connection
python scripts/odoo_connector.py --test-connection

# Create test invoice (dry run)
python scripts/odoo_connector.py --create-invoice \
  --customer "Test Customer" \
  --amount 100.00 \
  --dry-run

# Sync invoices
python scripts/odoo_connector.py --sync-invoices --last-days 30

# List customers
python scripts/odoo_connector.py --list-customers
```

---

## 📚 Odoo Models Reference

### account.move (Invoices)
```python
# Fields
- move_type: 'out_invoice' | 'in_invoice' | 'out_refund' | 'in_refund'
- partner_id: Customer/Vendor reference
- invoice_date: Invoice date
- amount_total: Total amount (with tax)
- amount_residual: Amount due
- state: 'draft' | 'posted' | 'paid' | 'cancelled'
- payment_state: 'not_paid' | 'partial' | 'paid'
```

### res.partner (Customers/Vendors)
```python
# Fields
- name: Partner name
- email: Email address
- phone: Phone number
- customer_rank: 1 if customer, 0 otherwise
- supplier_rank: 1 if vendor, 0 otherwise
```

### product.template (Products/Services)
```python
# Fields
- name: Product name
- type: 'product' | 'service' | 'consu'
- list_price: Sale price
- sale_ok: Can be sold
- purchase_ok: Can be purchased
```

---

## 🎯 Best Practices

1. **Always sync before creating** - Check if customer/invoice already exists
2. **Use dry-run for testing** - Test with `--dry-run` before actual operations
3. **Log everything** - All operations are logged for audit
4. **Respect approval thresholds** - Follow Company Handbook rules
5. **Handle errors gracefully** - Don't crash on API failures
6. **Sync regularly** - Keep local vault in sync with Odoo

---

## 📈 Performance Considerations

- **Rate Limiting:** Max 10 API calls per minute
- **Batch Operations:** Sync invoices in batches of 50
- **Caching:** Cache customer list for 1 hour
- **Timeout:** 30 second timeout for API calls

---

## 🔄 Integration Points

### With CEO Briefing
- Invoice data → Revenue analysis
- Customer count → Business growth metrics
- Payment status → Cash flow analysis

### With Email System
- Invoice creation → Send invoice via email
- Payment received → Send thank you email

### With Social Media
- New customer → Welcome post (with approval)
- Milestone → Celebration post

---

## 📝 Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-02 | Initial Gold Tier implementation |

---

*Odoo Connector Skill - Part of AI Employee Gold Tier*
