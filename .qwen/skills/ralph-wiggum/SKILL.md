# Ralph Wiggum Loop Skill

**Version:** 1.0.0  
**Type:** Gold Tier  
**Domain:** Task Persistence & Multi-Step Automation

---

## 📋 Overview

The Ralph Wiggum Loop implements a **Stop hook pattern** that keeps Qwen Code working autonomously until multi-step tasks are complete. Instead of exiting after one response, Qwen Code continues iterating until the task is done.

**Named after:** Ralph Wiggum from The Simpsons, who persistently says "I'm gonna keep trying until I get it right!"

---

## 🎯 Use Cases

### When to Use Ralph Wiggum Loop

1. **Multi-step tasks** that require several actions
2. **Batch processing** of multiple files
3. **Complex workflows** with dependencies
4. **Autonomous operation** without human intervention

### Examples

- "Process all files in Needs_Action folder"
- "Generate invoices for all pending requests"
- "Review and respond to all customer emails"
- "Sync all Odoo invoices and generate report"

---

## 🔧 How It Works

### The Loop Pattern

```
1. Orchestrator creates task with prompt
2. Qwen Code works on task
3. Qwen Code tries to exit
4. Stop hook checks: Is task complete?
   - Files moved to /Done?
   - Completion promise output?
   - No more items in Needs_Action?
5. If NO → Block exit, re-inject prompt
6. Repeat until complete or max iterations
```

### Completion Detection

The loop detects completion via:

1. **File Movement:** All files moved from `/Needs_Action` to `/Done`
2. **Completion Promise:** Qwen outputs specific string (e.g., `TASK_COMPLETE`)
3. **Pending Approval:** Items waiting for human approval

---

## 📖 Usage

### Basic Usage

```bash
python scripts/ralph_wiggum.py "Process all files in Needs_Action"
```

### With Custom Parameters

```bash
python scripts/ralph_wiggum.py \
  "Generate invoices for all pending requests" \
  --vault AI_Employee_Vault \
  --max-iterations 15 \
  --completion-promise "INVOICES_GENERATED"
```

### Dry Run (Testing)

```bash
python scripts/ralph_wiggum.py \
  "Process test files" \
  --dry-run
```

---

## 🎯 Integration with Orchestrator

### Enhanced Orchestrator Flow

```python
# In orchestrator.py

from ralph_wiggum import RalphWiggumLoop

# Instead of running Qwen once
# result = subprocess.run(['qwen', '--yolo', prompt])

# Use Ralph Wiggum Loop for persistence
loop = RalphWiggumLoop(
    vault_path=str(self.vault_path),
    max_iterations=10
)

success = loop.run(prompt)

if success:
    self.logger.info('Task completed successfully')
else:
    self.logger.warning('Task may not be fully complete')
```

---

## 📁 File Structure

```
AI_Employee_Vault/
├── Needs_Action/
│   ├── FILE_001.md          # Items to process
│   └── FILE_002.md
├── Done/
│   ├── FILE_001.md          # Completed items
│   └── FILE_002.md
├── Pending_Approval/
│   └── APPROVAL_001.md      # Waiting for human
└── Logs/
    └── ralph_wiggum_*.log   # Loop execution logs
```

---

## 🔄 Workflow Example

### Scenario: Process Invoice Requests

**Input:** 5 invoice requests in `/Needs_Action`

**Loop Execution:**

```
Iteration 1/10:
- Process FILE_001.md → Create invoice → Move to Done
- Process FILE_002.md → Create invoice → Move to Done
- 3 items remaining...

Iteration 2/10:
- Process FILE_003.md → Create invoice → Move to Done
- Process FILE_004.md → Need approval → Create approval request
- 1 item remaining...

Iteration 3/10:
- Process FILE_005.md → Create invoice → Move to Done
- 0 items remaining
- 1 approval pending
- Output: TASK_COMPLETE

[OK] Task complete: Waiting for approval: 1 items
```

---

## 🛡️ Configuration

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--vault` | AI_Employee_Vault | Path to Obsidian vault |
| `--max-iterations` | 10 | Maximum loop iterations |
| `--completion-promise` | TASK_COMPLETE | String indicating completion |
| `--dry-run` | False | Log without executing |

### Best Practices

1. **Set reasonable max_iterations:** 5-10 for most tasks
2. **Use specific completion promises:** Avoid false positives
3. **Monitor logs:** Check `/Logs/ralph_wiggum_*.log`
4. **Test with dry-run first:** Verify behavior before production

---

## 📊 Logging

### Log File Format

```
Logs/ralph_wiggum_2026-03-02.log
```

### Sample Log Entries

```log
2026-03-02 10:30:00 - RalphWiggumLoop - INFO - Initialized RalphWiggumLoop
2026-03-02 10:30:00 - RalphWiggumLoop - INFO - Vault: AI_Employee_Vault
2026-03-02 10:30:00 - RalphWiggumLoop - INFO - Max iterations: 10
2026-03-02 10:30:01 - RalphWiggumLoop - INFO - Starting Ralph Wiggum Loop
2026-03-02 10:30:01 - RalphWiggumLoop - INFO - Task: Process all files...
2026-03-02 10:30:05 - RalphWiggumLoop - INFO - Running Qwen Code (iteration 1/10)
2026-03-02 10:30:45 - RalphWiggumLoop - INFO - Qwen Code output length: 5432 chars
2026-03-02 10:30:45 - RalphWiggumLoop - INFO - ✗ Task not complete: 3 items pending
2026-03-02 10:30:47 - RalphWiggumLoop - INFO - Running Qwen Code (iteration 2/10)
...
2026-03-02 10:32:15 - RalphWiggumLoop - INFO - ✓ No items in Needs_Action - task complete
2026-03-02 10:32:15 - RalphWiggumLoop - INFO - Task completed: All items processed
```

---

## 🐛 Troubleshooting

### Loop Runs Forever

**Symptom:** Keeps iterating without completing

**Solutions:**
1. Check completion criteria - are files being moved to `/Done`?
2. Reduce `--max-iterations` to prevent infinite loops
3. Check for errors in Qwen Code output
4. Verify Company Handbook rules are clear

---

### Loop Exits Too Early

**Symptom:** Stops before all items processed

**Solutions:**
1. Check if completion promise appears in normal output
2. Use a more specific completion promise
3. Verify file movement detection is working
4. Check logs for completion reason

---

### Qwen Code Not Found

**Symptom:** Error: "Qwen Code not found"

**Solutions:**
```bash
# Verify installation
qwen --version

# Install if needed
npm install -g @anthropic/claude-code

# Check PATH
echo $PATH  # Linux/Mac
echo %PATH%  # Windows
```

---

## 🎯 Advanced Patterns

### Pattern 1: Batch Processing

```bash
# Process all pending items
python scripts/ralph_wiggum.py \
  "Process all files in Needs_Action folder" \
  --max-iterations 20
```

### Pattern 2: Conditional Completion

```python
# Custom completion check
def check_completion(output: str) -> bool:
    if "TASK_COMPLETE" in output:
        return True
    if needs_action_count == 0:
        return True
    if pending_approval_count > 0:
        return True  # Waiting for human
    return False
```

### Pattern 3: Multi-Domain Tasks

```bash
# Process emails AND create invoices
python scripts/ralph_wiggum.py \
  "Process emails in Needs_Action and create invoices for requests" \
  --completion-promise "ALL_DOMAINS_COMPLETE"
```

---

## 📈 Performance Metrics

### Typical Iteration Counts

| Task Type | Avg Iterations | Time per Iteration |
|-----------|----------------|-------------------|
| Simple file processing | 1-3 | 30-60 seconds |
| Batch invoices (10 items) | 3-5 | 45-90 seconds |
| Complex multi-step | 5-10 | 60-120 seconds |

### Optimization Tips

1. **Batch similar items** - Process all emails together
2. **Clear instructions** - Reduce Qwen confusion
3. **Company Handbook** - Define rules clearly
4. **Monitor and adjust** - Track iteration counts

---

## 🔐 Security Considerations

### Approval Workflow

The Ralph Wiggum Loop respects HITL:

```
If item requires approval:
  → Create file in /Pending_Approval
  → Do NOT execute action
  → Loop continues or completes (waiting for human)
```

### Rate Limiting

For external API calls:

```python
# Add delays between actions
time.sleep(1)  # Between API calls

# Track actions per iteration
if actions_this_iteration > MAX_ACTIONS:
    logger.warning("Rate limit approached, slowing down")
```

---

## 📝 Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-02 | Initial Gold Tier implementation |

---

## 📚 References

- **Blueprint Reference:** Section 2D - Persistence (The "Ralph Wiggum" Loop)
- **Original Implementation:** https://github.com/anthropics/claude-code/tree/main/.claude/plugins/ralph-wiggum
- **Pattern Documentation:** Stop hook pattern for autonomous agents

---

*Ralph Wiggum Loop Skill - Part of AI Employee Gold Tier*  
*"I'm gonna keep trying until I get it right!"*
