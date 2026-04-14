---
name: task-scheduler
description: |
  Schedule recurring tasks using cron (Linux/Mac) or Task Scheduler (Windows).
  Automates daily briefings, weekly audits, monthly reports, and periodic checks.
  Ensures AI Employee runs continuously without manual intervention.
---

# Task Scheduler Skill

Schedule recurring tasks for the AI Employee system.

## Purpose

Automate regular operations:
- Daily CEO Briefings (every morning at 7 AM)
- Weekly Business Audits (every Monday at 8 AM)
- Monthly Expense Reports (1st of each month)
- Hourly Watcher health checks

## Scheduling Options

### Option 1: Cron (Linux/Mac)

Edit crontab:
```bash
crontab -e
```

Add scheduled tasks:
```bash
# Daily CEO Briefing at 7 AM
0 7 * * * cd /path/to/scripts && python orchestrator.py /path/to/vault --generate-briefing

# Weekly Business Audit every Monday at 8 AM
0 8 * * 1 cd /path/to/scripts && python orchestrator.py /path/to/vault --weekly-audit

# Monthly Expense Report on 1st at 9 AM
0 9 1 * * cd /path/to/scripts && python orchestrator.py /path/to/vault --monthly-report

# Hourly health check
0 * * * * cd /path/to/scripts && python watchdog.py /path/to/vault
```

### Option 2: Windows Task Scheduler

Create scheduled tasks:

```powershell
# Daily CEO Briefing
schtasks /Create /TN "AI_Employee_Daily_Briefing" /TR "python C:\path\to\scripts\orchestrator.py C:\path\to\vault --generate-briefing" /SC DAILY /ST 07:00

# Weekly Business Audit
schtasks /Create /TN "AI_Employee_Weekly_Audit" /TR "python C:\path\to\scripts\orchestrator.py C:\path\to\vault --weekly-audit" /SC WEEKLY /D MON /ST 08:00

# Monthly Expense Report
schtasks /Create /TN "AI_Employee_Monthly_Report" /TR "python C:\path\to\scripts\orchestrator.py C:\path\to\vault --monthly-report" /SC MONTHLY /D 1 /ST 09:00
```

### Option 3: Python Scheduler (Cross-platform)

```bash
python scripts/scheduler_daemon.py --vault /path/to/vault
```

Runs as background service with built-in scheduler.

## Scheduled Tasks Reference

### Daily Tasks

| Task | Time | Command |
|------|------|---------|
| CEO Morning Briefing | 7:00 AM | `--generate-briefing` |
| Check Watchers Health | Every hour | `--health-check` |
| Process Overnight Items | 8:00 AM | `--process-backlog` |

### Weekly Tasks

| Task | Day/Time | Command |
|------|----------|---------|
| Business Audit | Monday 8 AM | `--weekly-audit` |
| Subscription Review | Friday 4 PM | `--subscription-audit` |
| Backup Vault | Sunday 2 AM | `--backup` |

### Monthly Tasks

| Task | Day/Time | Command |
|------|----------|---------|
| Expense Report | 1st, 9 AM | `--monthly-report` |
| Revenue Summary | 1st, 10 AM | `--revenue-report` |
| Clean Old Logs | 15th, 3 AM | `--cleanup-logs` |

## Scheduler Daemon Script

For systems without cron/Task Scheduler:

```bash
python scripts/scheduler_daemon.py \
  --vault /path/to/vault \
  --config /path/to/schedule_config.yaml
```

### Config File Format

```yaml
# schedule_config.yaml
schedules:
  - name: daily_briefing
    cron: "0 7 * * *"
    command: "--generate-briefing"
    
  - name: weekly_audit
    cron: "0 8 * * 1"
    command: "--weekly-audit"
    
  - name: monthly_report
    cron: "0 9 1 * *"
    command: "--monthly-report"
    
  - name: health_check
    cron: "0 * * * *"
    command: "--health-check"
```

## Generated Reports

### CEO Briefing (Daily)

Generated at 7 AM daily:

```markdown
---
generated: 2026-02-24T07:00:00Z
period: 2026-02-23
---

# Monday Morning CEO Briefing

## Executive Summary
Strong day with 3 invoices processed.

## Revenue
- **Today**: $1,500
- **MTD**: $4,500

## Completed Tasks
- [x] Processed 5 emails
- [x] Sent 2 invoices
- [x] Posted LinkedIn update

## Pending Approvals
- Payment to Vendor XYZ: $200

## Suggestions
- Cancel unused Notion subscription ($15/mo)
```

### Weekly Audit (Every Monday)

```markdown
---
generated: 2026-02-24T08:00:00Z
period: 2026-02-17 to 2026-02-23
---

# Weekly Business Audit

## This Week's Performance

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Revenue | $2,500 | $3,200 | ✅ |
| Tasks | 20 | 25 | ✅ |
| Response Time | <24h | 12h | ✅ |

## Subscription Audit
- Notion: No activity in 45 days - recommend cancellation
- Slack: Active daily - keep

## Recommendations
1. Cancel Notion subscription
2. Follow up on 2 overdue invoices
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Task not running | Check cron/Task Scheduler logs |
| Python not found | Use absolute path to python executable |
| Permission denied | Run scheduler with appropriate permissions |
| Missed execution | Check system was awake at scheduled time |

## Best Practices

1. **Log Everything**: All scheduled tasks should log to Files/Logs/
2. **Error Handling**: Failed tasks should alert human
3. **Idempotency**: Safe to re-run if missed
4. **Time Zones**: Use local time for business tasks
5. **Overlap Prevention**: Ensure tasks don't conflict

## Monitoring

Check scheduled task status:

```bash
# Cron jobs
crontab -l

# Windows Task Scheduler
schtasks /Query /TN "AI_Employee_*"

# Daemon status
ps aux | grep scheduler_daemon
```
