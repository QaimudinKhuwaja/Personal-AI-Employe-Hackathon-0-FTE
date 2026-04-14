# Ralph Wiggum Loop Guide

**Task Persistence for Multi-Step Automation**

---

## 📋 What is the Ralph Wiggum Loop?

The **Ralph Wiggum Loop** is a **Stop hook pattern** that keeps Qwen Code working autonomously until multi-step tasks are complete. Instead of exiting after one response, Qwen Code continues iterating until the task is done.

**Why "Ralph Wiggum"?** Named after The Simpsons character who persistently says "I'm gonna keep trying until I get it right!"

---

## 🎯 Problem It Solves

### Without Ralph Wiggum Loop

```
User: "Process all 10 files in Needs_Action"
Qwen: *Processes 1 file*
Qwen: "Done! (exits)"

User: "But there are 9 more files!"
Qwen: "Please run me again for each file"
```

### With Ralph Wiggum Loop

```
User: "Process all 10 files in Needs_Action"
Qwen: *Processes files in loop*
      Iteration 1: Processes 3 files
      Iteration 2: Processes 3 files
      Iteration 3: Processes 4 files
Qwen: "TASK_COMPLETE (all files processed)"

User: "Perfect! Everything done in one run!"
```

---

## 🚀 Quick Start

### Basic Usage

```bash
# Process all pending files
python scripts/ralph_wiggum.py "Process all files in Needs_Action"
```

### With Custom Options

```bash
python scripts/ralph_wiggum.py \
  "Generate invoices for all pending requests" \
  --vault AI_Employee_Vault \
  --max-iterations 15 \
  --completion-promise "INVOICES_DONE"
```

### Dry Run (Testing)

```bash
python scripts/ralph_wiggum.py \
  "Process test files" \
  --dry-run
```

---

## 📖 Usage Examples

### Example 1: Batch Email Processing

**Task:** Process 20 customer emails

```bash
python scripts/ralph_wiggum.py \
  "Read all email files in Needs_Action, draft replies, move to Done" \
  --max-iterations 10
```

**Expected Output:**
```
============================================================
RALPH WIGGUM LOOP - Task Persistence Mode
============================================================
Task: Read all email files in Needs_Action, draft replies...
Max iterations: 10
Completion signal: TASK_COMPLETE
============================================================

[Iteration 1/10]
[Running Qwen Code...]

[Iteration 2/10]
[Running Qwen Code...]

...

[OK] Task complete: All items processed

[SUCCESS] Task completed successfully!
```

### Example 2: Invoice Generation

**Task:** Create invoices for 5 requests

```bash
python scripts/ralph_wiggum.py \
  "For each invoice request in Needs_Action:
     1. Extract customer info and amount
     2. Create invoice in Odoo
     3. Log action
     4. Move file to Done" \
  --completion-promise "INVOICES_GENERATED"
```

### Example 3: Social Media Scheduling

**Task:** Schedule posts for the week

```bash
python scripts/ralph_wiggum.py \
  "Create social media posts for next week:
     - 3 LinkedIn posts
     - 3 Facebook posts
     - 2 Instagram posts
   Schedule them and log to vault" \
  --max-iterations 5
```

---

## 🔧 How It Works

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│              RALPH WIGGUM LOOP                          │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
            ┌────────────────────────┐
            │  1. Create Task Prompt │
            └───────────┬────────────┘
                        │
                        ▼
            ┌────────────────────────┐
            │  2. Run Qwen Code      │
            └───────────┬────────────┘
                        │
                        ▼
            ┌────────────────────────┐
            │  3. Check Completion   │
            │  - Files in Done?      │
            │  - Promise in output?  │
            │  - Waiting approval?   │
            └───────────┬────────────┘
                        │
            ┌───────────┴────────────┐
            │                        │
         YES │                    NO │
            ▼                        ▼
    ┌──────────────┐        ┌──────────────┐
    │ ✓ Complete   │        │ ↻ Loop Back  │
    │ Exit Loop    │        │ Re-inject    │
    └──────────────┘        └──────────────┘
```

### Completion Detection

The loop checks for completion after each iteration:

1. **File Movement Detection**
   - Are files moved from `/Needs_Action` to `/Done`?
   - Count remaining files

2. **Completion Promise**
   - Does Qwen output the completion string?
   - Default: `TASK_COMPLETE`

3. **Pending Approval**
   - Are items waiting for human approval?
   - If yes, task is "complete" (waiting on human)

---

## ⚙️ Configuration

### Parameters Reference

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `prompt` | str | Required | Task description for Qwen |
| `--vault` | str | AI_Employee_Vault | Path to Obsidian vault |
| `--max-iterations` | int | 10 | Maximum loop iterations |
| `--completion-promise` | str | TASK_COMPLETE | Completion signal string |
| `--dry-run` | flag | False | Log without executing |

### Best Practices

#### Setting Max Iterations

```bash
# Too low - may not complete
--max-iterations 2

# Good for simple tasks
--max-iterations 5

# Good for batch processing
--max-iterations 10

# Complex multi-domain tasks
--max-iterations 20
```

#### Choosing Completion Promise

```bash
# Generic (may have false positives)
--completion-promise "DONE"

# Better (less likely in normal output)
--completion-promise "TASK_COMPLETE"

# Best (unique, specific to task)
--completion-promise "INVOICES_GENERATED_2026"
--completion-promise "EMAILS_PROCESSED_BATCH_001"
```

---

## 🐛 Troubleshooting

### Loop Runs Max Iterations

**Symptom:** Always hits max iterations without completing

**Diagnosis:**
```bash
# Check if files are being moved
ls -la AI_Employee_Vault/Needs_Action/
ls -la AI_Employee_Vault/Done/

# Check Qwen output for errors
cat Logs/ralph_wiggum_*.log | grep -A 5 "Qwen Code"
```

**Solution:**
- Increase max_iterations
- Check if Qwen is actually processing files
- Verify file movement logic

### Loop Exits Immediately

**Symptom:** Exits after 1-2 iterations

**Diagnosis:**
```bash
# Check completion promise
cat Logs/ralph_wiggum_*.log | grep "Completion"
```

**Solution:**
- Use more specific completion promise
- Check if promise appears in normal output
- Verify completion detection logic

### Qwen Code Errors

**Symptom:** Qwen Code crashes or times out

**Diagnosis:**
```bash
# Check Qwen installation
qwen --version

# Check vault access
ls -la AI_Employee_Vault/

# Check logs for errors
cat Logs/ralph_wiggum_*.log | grep "Error"
```

**Solution:**
- Reinstall Qwen Code
- Fix file permissions
- Reduce timeout if needed

---

## 📚 References

- **Blueprint:** Section 2D - Persistence (The "Ralph Wiggum" Loop)
- **Original:** https://github.com/anthropics/claude-code/tree/main/.claude/plugins/ralph-wiggum
- **Pattern:** Stop hook for autonomous agents

---

*Ralph Wiggum Loop Guide - Personal AI Employee*
