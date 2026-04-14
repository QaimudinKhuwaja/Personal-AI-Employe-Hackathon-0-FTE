---
name: hitl-approval
description: |
  Human-in-the-Loop approval workflow for sensitive actions.
  Creates approval request files, waits for human approval via file movement,
  and executes approved actions. Essential for payments, new contacts, and irreversible actions.
---

# HITL Approval Workflow Skill

Human-in-the-Loop approval system for sensitive actions requiring human review.

## Purpose

Some actions are too sensitive for full automation. The HITL system:
1. Creates approval request files for sensitive actions
2. Waits for human to move file to Approved/ or Rejected/
3. Executes approved actions via MCP servers
4. Logs all decisions for audit trail

## Approval Triggers

| Action Type | Auto-Approve | Requires Approval |
|-------------|--------------|-------------------|
| Email to known contact | ✅ | - |
| Email to new contact | - | ❌ |
| Payment < $50 recurring | ✅ | - |
| Payment > $100 | - | ❌ |
| Payment to new recipient | - | ❌ |
| Social media scheduled post | ✅ | - |
| Social media reply/DM | - | ❌ |
| Delete files outside vault | - | ❌ |

## Folder Structure

```
AI_Employee_Vault/
├── Pending_Approval/    # Awaiting human decision
├── Approved/            # Approved, ready to execute
├── Rejected/            # Rejected, do not execute
└── Logs/                # Audit trail
```

## Approval File Format

```markdown
---
type: approval_request
action: payment
amount: 500.00
recipient: Client ABC
reference: Invoice #1234
created: 2026-02-24T10:30:00Z
expires: 2026-02-25T10:30:00Z
status: pending
priority: high
---

# 🔐 Approval Required: Payment to Client ABC

## Action Details

| Field | Value |
|-------|-------|
| **Action Type** | Payment |
| **Amount** | $500.00 |
| **Recipient** | Client ABC |
| **Bank** | XXXX1234 |
| **Reference** | Invoice #1234 |
| **Due Date** | 2026-02-28 |

## Reason

Payment for consulting services rendered in February 2026.
Invoice attached and verified against Company Handbook rules.

## Supporting Documents

- /Accounting/Invoices/Invoice_1234.pdf

## Risk Assessment

- ✅ Recipient is known client
- ✅ Invoice matches contract
- ✅ Amount within budget
- ⚠️ First payment to this recipient

## To Approve

Move this file to `/Approved` folder.

## To Reject

Move this file to `/Rejected` folder with reason.

## To Request Changes

Edit this file and add comments in the Notes section.

---
*Created by HITL Approval System*
```

## Human Workflow

### Approve an Action

1. Review the approval request file in `Pending_Approval/`
2. Verify all details are correct
3. Move file to `Approved/` folder

### Reject an Action

1. Open the approval request file
2. Add rejection reason in Notes section
3. Move file to `Rejected/` folder

### Request Changes

1. Open the approval request file
2. Add comments/questions in Notes section
3. Leave file in `Pending_Approval/`
4. Qwen Code will review and update

## Automated Execution

Once file is in `Approved/`:

```bash
# Orchestrator detects approved file
python scripts/orchestrator.py /path/to/vault

# Executes approved action via MCP
python scripts/execute_approved.py --file /path/to/Approved/PAYMENT_xxx.md
```

## Execution Logging

All executed actions are logged:

```json
{
  "timestamp": "2026-02-24T11:00:00Z",
  "action_type": "payment",
  "amount": 500.00,
  "recipient": "Client ABC",
  "approval_status": "approved",
  "approved_by": "human",
  "executed_by": "email_mcp",
  "result": "success"
}
```

## Expiration

Approval requests expire after 24 hours by default:
- Expired files moved to `Rejected/` with note
- Human notified of expiration
- Task re-queued if still needed

## Configuration

### Environment Variables

```bash
# Approval thresholds
AUTO_APPROVE_PAYMENT_LIMIT=50
REQUIRE_APPROVAL_PAYMENT_LIMIT=100

# Expiration
APPROVAL_EXPIRY_HOURS=24

# Notifications
ALERT_EMAIL=admin@company.com
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| File not executed | Check file is in Approved/ folder |
| Execution failed | Check Logs/ for error details |
| Approval expired | Re-create approval request |
| Wrong action executed | Review audit log, revert if needed |

## Security Notes

- Never auto-approve payments to new recipients
- Always require approval for irreversible actions
- Keep detailed audit logs
- Review rejected actions for patterns
