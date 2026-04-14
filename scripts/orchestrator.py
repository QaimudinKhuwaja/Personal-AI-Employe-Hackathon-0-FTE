"""
Orchestrator Module

Main orchestration script that triggers Qwen Code to process
items in the Needs_Action folder. This is the "brain" coordinator
for the AI Employee system.

Usage:
    python orchestrator.py /path/to/vault

Or with custom options:
    python orchestrator.py /path/to/vault --interval 60 --dry-run
"""

import os
import sys
import subprocess
import argparse
import logging
import time
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Tuple

# Add scripts folder to path for imports
scripts_dir = Path(__file__).parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

# Import Ralph Wiggum for multi-step task persistence
try:
    from ralph_wiggum import RalphWiggumLoop
    RALPH_WIGGUM_AVAILABLE = True
except ImportError:
    RALPH_WIGGUM_AVAILABLE = False
    RalphWiggumLoop = None

# Import Calendar Tool for scheduling integration
try:
    from calendar_tool import CalendarTool
    CALENDAR_AVAILABLE = True
except ImportError:
    CALENDAR_AVAILABLE = False
    CalendarTool = None

# Import QuarantineManager for failed task handling
try:
    from retry_handler import QuarantineManager
    QUARANTINE_AVAILABLE = True
except ImportError:
    QUARANTINE_AVAILABLE = False
    QuarantineManager = None


class Orchestrator:
    """
    Orchestrates Qwen Code processing of action items.

    Monitors the Needs_Action folder and triggers Qwen Code
    to process pending items according to the Company Handbook rules.
    """
    
    def __init__(
        self,
        vault_path: str,
        check_interval: int = 60,
        dry_run: bool = False,
        use_ralph_wiggum: bool = True,
        max_ralph_iterations: int = 5,
        completion_promise: str = 'TASK_COMPLETE',
        max_failures_before_quarantine: int = 3,
        auto_quarantine: bool = True
    ):
        """
        Initialize the orchestrator.

        Args:
            vault_path: Path to the Obsidian vault root directory
            check_interval: Seconds between checks (default: 60)
            dry_run: If True, log actions without executing (default: False)
            use_ralph_wiggum: If True, use Ralph Wiggum pattern for multi-step tasks (default: True)
            max_ralph_iterations: Maximum iterations per task (default: 5)
            completion_promise: String that indicates task completion (default: 'TASK_COMPLETE')
            max_failures_before_quarantine: Failures before quarantining (default: 3)
            auto_quarantine: If True, auto-quarantine failed items (default: True)
        """
        self.vault_path = Path(vault_path)
        self.check_interval = check_interval
        self.dry_run = dry_run
        self.use_ralph_wiggum = use_ralph_wiggum and RALPH_WIGGUM_AVAILABLE
        self.max_ralph_iterations = max_ralph_iterations
        self.completion_promise = completion_promise
        self.max_failures_before_quarantine = max_failures_before_quarantine
        self.auto_quarantine = auto_quarantine and QUARANTINE_AVAILABLE
        
        # Define folders
        self.needs_action = self.vault_path / 'Needs_Action'
        self.done = self.vault_path / 'Done'
        self.plans = self.vault_path / 'Plans'
        self.logs = self.vault_path / 'Logs'
        self.dashboard = self.vault_path / 'Dashboard.md'
        self.handbook = self.vault_path / 'Company_Handbook.md'
        self.goals = self.vault_path / 'Business_Goals.md'
        
        # Ensure directories exist
        for folder in [self.needs_action, self.done, self.plans, self.logs]:
            folder.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self._setup_logging()

        self.logger.info(f'Initialized Orchestrator')
        self.logger.info(f'Vault: {self.vault_path}')
        self.logger.info(f'Dry run: {self.dry_run}')
        self.logger.info(f'Ralph Wiggum: {self.use_ralph_wiggum} (max {self.max_ralph_iterations} iterations)')
        self.logger.info(f'Auto-Quarantine: {self.auto_quarantine} (after {self.max_failures_before_quarantine} failures)')

        # Ralph Wiggum loop instance (initialized lazily)
        self._ralph_loop: Optional['RalphWiggumLoop'] = None
        
        # Calendar tool instance (initialized lazily)
        self._calendar: Optional['CalendarTool'] = None
        
        # Quarantine manager instance (initialized lazily)
        self._quarantine_mgr: Optional['QuarantineManager'] = None
        
        # Track failure counts per item
        self._failure_counts: dict = {}
    
    def _setup_logging(self):
        """Setup logging to file and console."""
        log_file = self.logs / f'orchestrator_{datetime.now().strftime("%Y-%m-%d")}.log'

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ],
            encoding='utf-8'
        )
        self.logger = logging.getLogger('Orchestrator')
    
    def get_pending_items(self) -> List[Path]:
        """
        Get all pending action files in Needs_Action folder.
        
        Returns:
            List of Path objects for pending action files
        """
        if not self.needs_action.exists():
            return []
        
        pending = []
        for filepath in self.needs_action.iterdir():
            if filepath.is_file() and filepath.suffix == '.md':
                # Skip hidden files
                if not filepath.name.startswith('.'):
                    pending.append(filepath)
        
        return sorted(pending, key=lambda p: p.stat().st_mtime)
    
    def process_items(self, items: List[Path]) -> Tuple[int, int]:
        """
        Process a list of action items using Qwen Code.
        
        If Ralph Wiggum is enabled and there are multiple items,
        uses the persistence loop to ensure all tasks complete.
        
        Failed items are tracked and quarantined after max failures.

        Args:
            items: List of action file paths to process

        Returns:
            Tuple of (successful_count, failed_count)
        """
        if not items:
            self.logger.info('No items to process')
            return (0, 0)

        self.logger.info(f'Processing {len(items)} item(s)')

        # If Ralph Wiggum is enabled and we have multiple items, use persistence loop
        if self.use_ralph_wiggum and len(items) > 0:
            return self._process_with_ralph_wiggum(items)

        # Otherwise, process items one by one (original behavior)
        successful = 0
        failed = 0

        for item in items:
            try:
                result = self._process_single_item(item)
                if result:
                    successful += 1
                    # Reset failure count on success
                    if item.name in self._failure_counts:
                        del self._failure_counts[item.name]
                else:
                    failed += 1
                    # Track failure and potentially quarantine
                    self._quarantine_failed_item(item, 'Processing returned failure')
            except Exception as e:
                self.logger.error(f'Failed to process {item.name}: {e}')
                failed += 1
                # Track failure and potentially quarantine
                self._quarantine_failed_item(item, str(e))

        return (successful, failed)

    def _process_with_ralph_wiggum(self, items: List[Path]) -> Tuple[int, int]:
        """
        Process items using Ralph Wiggum persistence loop.

        This method:
        1. Builds a prompt for all pending items
        2. Runs Ralph Wiggum loop until all items processed
        3. Logs detailed iteration results

        Args:
            items: List of action file paths to process

        Returns:
            Tuple of (successful_count, failed_count)
        """
        task_description = f'Process {len(items)} action item(s) from Needs_Action folder'

        # Build comprehensive prompt for all items
        prompt = self._build_multi_item_prompt(items)

        # Run Ralph Wiggum loop
        ralph_result = self._run_ralph_wiggum_loop(prompt, task_description)

        # Determine success based on completion
        if ralph_result['success']:
            # All items should be processed - verify by checking Needs_Action
            remaining = self.get_pending_items()
            processed_count = len(items) - len(remaining)

            self.logger.info(f'Ralph Wiggum completed: {processed_count}/{len(items)} items processed')
            self.logger.info(f'Completion reason: {ralph_result["completion_reason"]}')

            # Log iteration summary
            for i, output in enumerate(ralph_result['output_per_iteration'], 1):
                if output:
                    self.logger.info(f'Iteration {i} output length: {len(output)} chars')

            return (processed_count, len(items) - processed_count)
        else:
            # Max iterations reached - check what was actually processed
            remaining = self.get_pending_items()
            processed_count = len(items) - len(remaining)

            self.logger.warning(f'Ralph Wiggum incomplete: {processed_count}/{len(items)} processed')
            self.logger.warning(f'Stopped because: {ralph_result["completion_reason"]}')

            return (processed_count, len(items) - processed_count)

    def _build_multi_item_prompt(self, items: List[Path]) -> str:
        """
        Build prompt for multiple action items.

        Args:
            items: List of action file paths

        Returns:
            Formatted prompt string
        """
        # Read company handbook
        handbook_content = ""
        if self.handbook.exists():
            handbook_content = self.handbook.read_text(encoding='utf-8')

        # Read business goals
        goals_content = ""
        if self.goals.exists():
            goals_content = self.goals.read_text(encoding='utf-8')

        # Build items list
        items_content = ""
        for i, item in enumerate(items, 1):
            try:
                content = item.read_text(encoding='utf-8')
                items_content += f"\n### Item {i}: {item.name}\n\n```markdown\n{content}\n```\n\n"
            except Exception as e:
                self.logger.warning(f'Could not read {item.name}: {e}')
                items_content += f"\n### Item {i}: {item.name}\n\n[Error reading file]\n\n"

        prompt = f"""You are the AI Employee assistant. Process ALL action items in the Needs_Action folder.

## Items to Process ({len(items)} total)

{items_content}

## Company Handbook Rules

```markdown
{handbook_content if handbook_content else "No handbook found"}
```

## Business Goals

```markdown
{goals_content if goals_content else "No business goals found"}
```

## Your Instructions

1. Read and understand EACH action file listed above
2. Check the Company Handbook for relevant rules
3. For EACH item:
   - Determine what actions need to be taken
   - If the action requires approval, create an approval request file in /Pending_Approval
   - If the action can be done autonomously, do it now
   - When complete, move the action file to /Done folder
4. Update the Dashboard.md with the current status after processing ALL items
5. Log all actions taken

## Important

- Process ALL items - do not stop until every single item is handled
- Be concise and professional
- Follow all Company Handbook rules
- When in doubt, request approval rather than guessing
- Always log what you did

Begin processing all items now.
"""

        return prompt
    
    def _process_single_item(self, item: Path) -> bool:
        """
        Process a single action item with Qwen Code.

        Args:
            item: Path to the action file

        Returns:
            True if processing succeeded, False otherwise
        """
        self.logger.info(f'Processing: {item.name}')

        if self.dry_run:
            self.logger.info(f'[DRY RUN] Would process: {item.name}')
            return True

        try:
            # Build the Qwen Code command
            # Qwen reads the action file, company handbook, and processes the request
            prompt = self._build_prompt(item)

            # Run Qwen Code with the prompt
            result = self._run_qwen_code(prompt)

            if result.returncode == 0:
                self.logger.info(f'Successfully processed: {item.name}')
                return True
            else:
                self.logger.warning(f'Qwen Code returned non-zero: {result.returncode}')
                if result.stderr:
                    self.logger.error(f'Stderr: {result.stderr[:1000]}')
                if result.stdout:
                    self.logger.info(f'Stdout: {result.stdout[:500]}')
                return False

        except FileNotFoundError as e:
            self.logger.error(f'FileNotFoundError: {e}')
            self.logger.error('Qwen Code not found. Please ensure Qwen Code is installed and in PATH.')
            return False
        except Exception as e:
            self.logger.error(f'Error processing item: {e}', exc_info=True)
            return False
    
    def _build_prompt(self, item: Path) -> str:
        """
        Build the prompt for Qwen Code.

        Args:
            item: Path to the action file

        Returns:
            Formatted prompt string
        """
        # Read the action file
        action_content = item.read_text(encoding='utf-8')
        
        # Read company handbook if exists
        handbook_content = ""
        if self.handbook.exists():
            handbook_content = self.handbook.read_text(encoding='utf-8')
        
        # Read business goals if exists
        goals_content = ""
        if self.goals.exists():
            goals_content = self.goals.read_text(encoding='utf-8')
        
        prompt = f"""You are the AI Employee assistant. Process the following action item according to the Company Handbook rules.

## Current Task

Process this action file from the Needs_Action folder:

```markdown
{action_content}
```

## Company Handbook Rules

```markdown
{handbook_content if handbook_content else "No handbook found"}
```

## Business Goals

```markdown
{goals_content if goals_content else "No business goals found"}
```

## Your Instructions

1. Read and understand the action file
2. Check the Company Handbook for relevant rules
3. Determine what actions need to be taken
4. If the action requires approval, create an approval request file in /Pending_Approval
5. If the action can be done autonomously, do it now
6. Update the Dashboard.md with the current status
7. When complete, move this action file to /Done folder
8. Log all actions taken

## Output Format

- Be concise and professional
- Follow all Company Handbook rules
- When in doubt, request approval rather than guessing
- Always log what you did

Begin processing now.
"""
        
        return prompt
    
    def _run_qwen_code(self, prompt: str) -> subprocess.CompletedProcess:
        """
        Run Qwen Code with the given prompt.

        Args:
            prompt: The prompt to send to Qwen Code

        Returns:
            CompletedProcess result
        """
        import tempfile
        
        # Change to vault directory so Qwen can access files
        cwd = str(self.vault_path)

        self.logger.info(f'Running Qwen Code in {cwd}')

        # Write prompt to a temp file to avoid command line length limits
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(prompt)
            temp_file = f.name
        
        try:
            # Run Qwen Code with stdin from file
            # Use shell=True on Windows for better command handling
            cmd = f'type "{temp_file}" | qwen --yolo'

            # Run Qwen Code
            result = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                shell=True,  # Use shell for better Windows compatibility
                encoding='utf-8',
                errors='replace'
            )

            return result
        finally:
            # Clean up temp file
            import os
            if os.path.exists(temp_file):
                os.remove(temp_file)
    
    def _get_ralph_loop(self) -> Optional['RalphWiggumLoop']:
        """
        Get or create Ralph Wiggum loop instance.

        Returns:
            RalphWiggumLoop instance or None if unavailable
        """
        if not self.use_ralph_wiggum:
            return None

        if self._ralph_loop is None and RALPH_WIGGUM_AVAILABLE and RalphWiggumLoop is not None:
            try:
                self._ralph_loop = RalphWiggumLoop(
                    vault_path=str(self.vault_path),
                    max_iterations=self.max_ralph_iterations,
                    completion_promise=self.completion_promise,
                    dry_run=self.dry_run
                )
                self.logger.info('Ralph Wiggum loop initialized')
            except Exception as e:
                self.logger.warning(f'Failed to initialize Ralph Wiggum loop: {e}')
                self._ralph_loop = None

        return self._ralph_loop

    def _check_task_completion(self) -> Tuple[bool, str]:
        """
        Check if all tasks are complete using multiple strategies.

        Strategies:
        1. No more items in Needs_Action
        2. Items waiting for approval in Pending_Approval

        Returns:
            Tuple of (is_complete, reason)
        """
        # Strategy 1: Check if Needs_Action is empty
        needs_action_count = len(list(self.needs_action.glob('*.md')))

        if needs_action_count == 0:
            return (True, 'All items processed')

        # Strategy 2: Check if there are only approval requests (waiting for human)
        pending_approval = self.vault_path / 'Pending_Approval'
        if pending_approval.exists():
            pending_count = len(list(pending_approval.glob('*.md')))
            if pending_count > 0 and needs_action_count == 0:
                return (True, f'Waiting for approval: {pending_count} items')

        # Task not complete
        return (False, f'{needs_action_count} items remaining')

    def _run_ralph_wiggum_loop(self, prompt: str, task_description: str) -> dict:
        """
        Run Ralph Wiggum persistence loop for a multi-step task.

        This method:
        1. Checks if Ralph Wiggum is available and enabled
        2. Runs iterations until completion or max iterations
        3. Logs each iteration with timestamps and status
        4. Returns detailed results

        Args:
            prompt: The prompt to send to Qwen Code
            task_description: Human-readable task description

        Returns:
            Dictionary with results:
            - success: bool
            - iterations: int
            - completion_reason: str
            - output_per_iteration: list of strings
        """
        result = {
            'success': False,
            'iterations': 0,
            'completion_reason': '',
            'output_per_iteration': [],
            'task_description': task_description,
            'start_time': datetime.now().isoformat(),
            'end_time': None
        }

        self.logger.info(f'='*60)
        self.logger.info(f'RALPH WIGGUM LOOP - Multi-Step Task Persistence')
        self.logger.info(f'Task: {task_description}')
        self.logger.info(f'Max iterations: {self.max_ralph_iterations}')
        self.logger.info(f'Completion signal: {self.completion_promise}')
        self.logger.info(f'='*60)

        print(f"\n{'='*60}")
        print(f"🔄 RALPH WIGGUM LOOP - Task Persistence Mode")
        print(f"{'='*60}")
        print(f"Task: {task_description}")
        print(f"Max iterations: {self.max_ralph_iterations}")
        print(f"Completion signal: {self.completion_promise}")
        print(f"{'='*60}\n")

        iteration_outputs = []

        for iteration in range(1, self.max_ralph_iterations + 1):
            iteration_start = datetime.now()
            result['iterations'] = iteration

            self.logger.info(f'\n[Iteration {iteration}/{self.max_ralph_iterations}] Starting...')
            print(f"\n[Iteration {iteration}/{self.max_ralph_iterations}] Starting...")

            # Check completion before running
            is_complete, reason = self._check_task_completion()

            if is_complete:
                self.logger.info(f'✓ Task complete before iteration {iteration}: {reason}')
                print(f"\n[OK] Task complete: {reason}")
                result['success'] = True
                result['completion_reason'] = reason
                result['end_time'] = datetime.now().isoformat()
                return result

            # Run Qwen Code with enhanced Ralph Wiggum prompt
            ralph_prompt = self._build_ralph_wiggum_prompt(prompt, iteration)

            self.logger.info(f'Running Qwen Code with Ralph Wiggum instructions...')
            print(f"[Running Qwen Code...]")

            output = ''
            try:
                qwen_result = self._run_qwen_code(ralph_prompt)
                output = qwen_result.stdout if qwen_result.stdout else ''
                if qwen_result.stderr:
                    output += '\n' + qwen_result.stderr
            except Exception as e:
                self.logger.error(f'Qwen Code execution error: {e}')
                output = f'Error: {str(e)}'

            iteration_outputs.append(output)
            result['output_per_iteration'].append(output[:2000])  # Truncate for storage

            # Check for completion promise in output
            if self.completion_promise in output:
                self.logger.info(f'✓ Completion promise detected: "{self.completion_promise}"')
                print(f"\n[OK] Completion promise detected!")
                result['success'] = True
                result['completion_reason'] = 'Completion promise found in output'
                result['end_time'] = datetime.now().isoformat()
                return result

            # Check task completion via file system
            is_complete, reason = self._check_task_completion()

            if is_complete:
                self.logger.info(f'✓ Task complete after iteration {iteration}: {reason}')
                print(f"\n[OK] Task complete: {reason}")
                result['success'] = True
                result['completion_reason'] = reason
                result['end_time'] = datetime.now().isoformat()
                return result

            iteration_duration = (datetime.now() - iteration_start).total_seconds()
            self.logger.info(f'Iteration {iteration} completed in {iteration_duration:.1f}s, continuing...')
            print(f"[Iteration {iteration}] Completed in {iteration_duration:.1f}s - continuing...")

            # Small delay before next iteration
            time.sleep(2)

        # Max iterations reached
        result['end_time'] = datetime.now().isoformat()
        self.logger.warning(f'⚠ Max iterations ({self.max_ralph_iterations}) reached without completion')
        print(f"\n{'='*60}")
        print(f"⚠️  Max iterations reached")
        print(f"Task may not be fully complete")
        print(f"{'='*60}\n")

        result['completion_reason'] = 'Max iterations reached'
        return result

    def _build_ralph_wiggum_prompt(self, base_prompt: str, iteration: int) -> str:
        """
        Build enhanced prompt with Ralph Wiggum persistence instructions.

        Args:
            base_prompt: Original task prompt
            iteration: Current iteration number

        Returns:
            Enhanced prompt with persistence instructions
        """
        return f"""{base_prompt}

## IMPORTANT: Task Persistence Mode (Ralph Wiggum Pattern - Iteration {iteration}/{self.max_ralph_iterations})

You are in **Task Persistence Mode**. This means:

1. **DO NOT exit** until the task is fully complete
2. **Keep working** through multiple steps if needed
3. **Move files to /Done** when you finish processing them
4. **Output "{self.completion_promise}"** when the entire task is complete

### Your Workflow

1. Read all files in /Needs_Action
2. Process each file according to Company Handbook rules
3. For each file:
   - If it requires approval → Create file in /Pending_Approval
   - If it can be done autonomously → Do it now
   - When done → Move file to /Done
4. Update Dashboard.md with progress
5. Log all actions to /Logs
6. **Repeat** until all files are processed
7. **Output "{self.completion_promise}"** when completely done

### Current Status

- This is iteration {iteration} of {self.max_ralph_iterations}
- If there are still items in /Needs_Action, **keep working**
- If you are waiting for approval, **stop and wait**
- If all items are processed, **output "{self.completion_promise}"**

Begin processing now.
"""

    def _get_calendar(self) -> Optional['CalendarTool']:
        """
        Get or create Calendar tool instance.

        Returns:
            CalendarTool instance or None if unavailable
        """
        if not CALENDAR_AVAILABLE:
            return None

        if self._calendar is None and CalendarTool is not None:
            try:
                self._calendar = CalendarTool(vault_path=str(self.vault_path))
                self.logger.info('Calendar tool initialized')
            except Exception as e:
                self.logger.warning(f'Failed to initialize calendar tool: {e}')
                self._calendar = None

        return self._calendar

    def schedule_event(
        self,
        title: str,
        start: str,
        end: str,
        description: str = '',
        location: str = '',
        categories: List[str] = None,
        dry_run: bool = False
    ) -> dict:
        """
        Schedule a new calendar event.

        This method integrates with the Calendar MCP workflow by:
        1. Creating the event in the local calendar
        2. Optionally checking for conflicts
        3. Logging the scheduling action

        Args:
            title: Event title
            start: Start datetime (YYYY-MM-DDTHH:MM:SS)
            end: End datetime (YYYY-MM-DDTHH:MM:SS)
            description: Event description
            location: Event location
            categories: Categories/tags
            dry_run: If True, simulate without creating

        Returns:
            Dictionary with event details or error
        """
        cal = self._get_calendar()
        if not cal:
            return {'error': 'Calendar tool not available'}

        try:
            # Check for conflicts before creating
            conflicts = cal.check_conflicts(start, end)
            has_conflicts = len(conflicts) > 0

            if has_conflicts and not dry_run:
                self.logger.warning(f'Scheduling conflict detected for {title} at {start}')
                self.logger.warning(f'Conflicts with: {", ".join([c["title"] for c in conflicts])}')

            # Create event
            event = cal.create_event(
                title=title,
                start=start,
                end=end,
                description=description,
                location=location,
                categories=categories or [],
                dry_run=dry_run
            )

            # Add conflict info to result
            event['has_conflicts'] = has_conflicts
            event['conflicts'] = conflicts

            self.logger.info(f'Scheduled event: {title} at {start}')
            if has_conflicts:
                self.logger.warning(f'Event has {len(conflicts)} scheduling conflict(s)')

            return event

        except Exception as e:
            self.logger.error(f'Failed to schedule event: {e}')
            return {'error': str(e)}

    def get_upcoming_events(self, days: int = 7) -> List[dict]:
        """
        Get upcoming calendar events.

        Args:
            days: Number of days ahead to look

        Returns:
            List of upcoming event dictionaries
        """
        cal = self._get_calendar()
        if not cal:
            return []

        try:
            events = cal.list_events(days=days)
            self.logger.info(f'Found {len(events)} upcoming events')
            return events
        except Exception as e:
            self.logger.error(f'Failed to get upcoming events: {e}')
            return []

    def check_schedule_conflicts(self, start: str, end: str, exclude_id: str = None) -> List[dict]:
        """
        Check for scheduling conflicts.

        Args:
            start: Start of time range
            end: End of time range
            exclude_id: Event ID to exclude

        Returns:
            List of conflicting events
        """
        cal = self._get_calendar()
        if not cal:
            return []

        try:
            conflicts = cal.check_conflicts(start, end, exclude_id)
            return conflicts
        except Exception as e:
            self.logger.error(f'Failed to check conflicts: {e}')
            return []

    def get_day_schedule(self, date: str) -> List[dict]:
        """
        Get schedule for a specific day.

        Args:
            date: Date string (YYYY-MM-DD)

        Returns:
            List of events for that day
        """
        cal = self._get_calendar()
        if not cal:
            return []

        try:
            events = cal.get_day_schedule(date)
            self.logger.info(f'Found {len(events)} events on {date}')
            return events
        except Exception as e:
            self.logger.error(f'Failed to get day schedule: {e}')
            return []

    def _get_quarantine_manager(self) -> Optional['QuarantineManager']:
        """
        Get or create QuarantineManager instance.

        Returns:
            QuarantineManager instance or None if unavailable
        """
        if not self.auto_quarantine:
            return None

        if self._quarantine_mgr is None and QuarantineManager is not None:
            try:
                quarantine_path = self.vault_path / 'Quarantine'
                self._quarantine_mgr = QuarantineManager(
                    quarantine_dir=str(quarantine_path)
                )
                self.logger.info('Quarantine manager initialized')
            except Exception as e:
                self.logger.warning(f'Failed to initialize quarantine manager: {e}')
                self._quarantine_mgr = None

        return self._quarantine_mgr

    def _quarantine_failed_item(
        self,
        item_path: Path,
        error: str,
        attempts: int = 1
    ) -> Optional[Path]:
        """
        Move a failed item to quarantine.

        This method:
        1. Tracks failure count for the item
        2. Quarantines if max failures reached
        3. Logs the quarantine action with full metadata
        4. Moves original file from Needs_Action to Quarantine

        Args:
            item_path: Path to the failed item
            error: Error message describing the failure
            attempts: Number of failed attempts

        Returns:
            Path to quarantined file, or None if not quarantined
        """
        # Track failure count
        item_key = item_path.name
        self._failure_counts[item_key] = self._failure_counts.get(item_key, 0) + 1
        current_attempts = self._failure_counts[item_key]

        # Check if we should quarantine
        if current_attempts < self.max_failures_before_quarantine:
            self.logger.warning(
                f'Item {item_path.name} failed (attempt {current_attempts}/{self.max_failures_before_quarantine}) - not yet quarantining'
            )
            return None

        # Get quarantine manager
        qm = self._get_quarantine_manager()
        if not qm:
            self.logger.error('Quarantine manager not available')
            return None

        self.logger.warning(
            f'Quarantining {item_path.name} after {current_attempts} failures'
        )

        try:
            # Quarantine the item
            quarantine_path = qm.quarantine(
                item_id=item_path.stem,
                item_type=item_path.suffix.lstrip('.') or 'action',
                error=error,
                attempts=current_attempts,
                original_path=item_path
            )

            # Move original file to quarantine
            if item_path.exists():
                dest = self.vault_path / 'Quarantine' / item_path.name
                item_path.rename(dest)
                self.logger.info(f'Moved {item_path.name} to Quarantine/')

            # Reset failure count
            del self._failure_counts[item_key]

            self.logger.info(f'Item quarantined: {item_path.name} -> {quarantine_path}')
            return quarantine_path

        except Exception as e:
            self.logger.error(f'Failed to quarantine item {item_path.name}: {e}')
            return None

    def list_quarantined_items(self) -> List[dict]:
        """
        List all quarantined items.

        Returns:
            List of quarantined item metadata dictionaries
        """
        qm = self._get_quarantine_manager()
        if not qm:
            return []

        try:
            items = qm.list_quarantined()
            self.logger.info(f'Found {len(items)} quarantined items')
            return items
        except Exception as e:
            self.logger.error(f'Failed to list quarantined items: {e}')
            return []

    def release_quarantined_item(self, item_file: str, destination: str = 'Needs_Action') -> bool:
        """
        Release an item from quarantine.

        Args:
            item_file: Path to quarantined item file
            destination: Destination folder (default: Needs_Action)

        Returns:
            True if released successfully
        """
        qm = self._get_quarantine_manager()
        if not qm:
            return False

        try:
            dest_path = self.vault_path / destination
            success = qm.release(item_file, str(dest_path))

            if success:
                self.logger.info(f'Released quarantined item to {destination}/')
            return success

        except Exception as e:
            self.logger.error(f'Failed to release quarantined item: {e}')
            return False

    def purge_old_quarantined(self, days_old: int = 30) -> int:
        """
        Purge quarantined items older than specified days.

        Args:
            days_old: Age threshold in days

        Returns:
            Number of items purged
        """
        qm = self._get_quarantine_manager()
        if not qm:
            return 0

        quarantine_dir = qm.quarantine_dir
        purged = 0
        cutoff = datetime.now() - timedelta(days=days_old)

        try:
            for item_file in quarantine_dir.glob('*.md'):
                mtime = datetime.fromtimestamp(item_file.stat().st_mtime)
                if mtime < cutoff:
                    item_file.unlink()
                    purged += 1
                    self.logger.info(f'Purged old quarantined item: {item_file.name}')

            self.logger.info(f'Purged {purged} quarantined items older than {days_old} days')
            return purged

        except Exception as e:
            self.logger.error(f'Failed to purge old quarantined items: {e}')
            return 0

    def get_quarantine_status(self) -> dict:
        """
        Get current quarantine status.

        Returns:
            Dictionary with quarantine statistics
        """
        quarantine_dir = self.vault_path / 'Quarantine'

        status = {
            'enabled': self.auto_quarantine,
            'max_failures_before_quarantine': self.max_failures_before_quarantine,
            'quarantine_path': str(quarantine_dir),
            'total_quarantined': 0,
            'items_pending_failure': {},
            'recent_quarantines': []
        }

        # Count quarantined items
        if quarantine_dir.exists():
            status['total_quarantined'] = len(list(quarantine_dir.glob('*.md')))

            # Get recent quarantines
            recent = []
            for item_file in sorted(quarantine_dir.glob('*.md'), key=lambda f: f.stat().st_mtime, reverse=True)[:5]:
                recent.append({
                    'file': item_file.name,
                    'quarantined_at': datetime.fromtimestamp(item_file.stat().st_mtime).isoformat()
                })
            status['recent_quarantines'] = recent

        # Add items with pending failures
        status['items_pending_failure'] = dict(self._failure_counts)

        return status

    def update_dashboard(self, processed: int, success: int, failed: int):
        """
        Update the Dashboard.md with processing summary.

        Args:
            processed: Number of items processed
            success: Number of successful operations
            failed: Number of failed operations
        """
        if self.dry_run:
            self.logger.info(f'[DRY RUN] Would update dashboard')
            return
        
        if not self.dashboard.exists():
            self.logger.warning('Dashboard.md not found')
            return
        
        try:
            content = self.dashboard.read_text(encoding='utf-8')
            
            # Update the Quick Status section
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Find and update the status line
            if '**Last Activity**' in content:
                content = content.replace(
                    '**Last Activity** | - | -',
                    f'**Last Activity** | {timestamp} | Processing complete'
                )
            
            # Add to recent activity table
            activity_line = f'| {timestamp} | Batch processed {processed} items | {"✅" if failed == 0 else "⚠️"} |\n'
            
            # Find the Recent Activity section and add entry
            if '| - | - | - |' in content:
                content = content.replace(
                    '| - | - | - |',
                    activity_line + '| - | - | - |'
                )
            
            # Update pending tasks count
            pending_count = len(self.get_pending_items())
            if '**Pending Tasks**' in content:
                content = content.replace(
                    '**Pending Tasks** | 0 | -',
                    f'**Pending Tasks** | {pending_count} | {"⚠️" if pending_count > 0 else "🟢"}'
                )
            
            self.dashboard.write_text(content, encoding='utf-8')
            self.logger.info('Dashboard updated')
            
        except Exception as e:
            self.logger.error(f'Failed to update dashboard: {e}')
    
    def run(self):
        """
        Main run loop for the orchestrator.
        
        Continuously checks for pending items and processes them.
        """
        self.logger.info('Starting Orchestrator')
        self.logger.info(f'Check interval: {self.check_interval}s')
        
        try:
            while True:
                try:
                    # Get pending items
                    pending = self.get_pending_items()
                    
                    if pending:
                        # Process items
                        success, failed = self.process_items(pending)
                        
                        # Update dashboard
                        self.update_dashboard(len(pending), success, failed)
                    else:
                        self.logger.debug('No pending items')
                    
                    # Wait for next check
                    import time
                    time.sleep(self.check_interval)
                    
                except Exception as e:
                    self.logger.error(f'Error in processing loop: {e}', exc_info=True)
                    import time
                    time.sleep(self.check_interval)
                    
        except KeyboardInterrupt:
            self.logger.info('Orchestrator stopped by user')
        except Exception as e:
            self.logger.error(f'Fatal error: {e}', exc_info=True)
            raise


def main():
    """Main entry point for the orchestrator."""
    parser = argparse.ArgumentParser(
        description='AI Employee Orchestrator'
    )
    parser.add_argument(
        'vault_path',
        type=str,
        help='Path to the Obsidian vault root directory'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=60,
        help='Check interval in seconds (default: 60)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Log actions without executing (for testing)'
    )
    parser.add_argument(
        '--once',
        action='store_true',
        help='Run once and exit (for testing)'
    )
    parser.add_argument(
        '--no-ralph-wiggum',
        action='store_true',
        help='Disable Ralph Wiggum persistence loop'
    )
    parser.add_argument(
        '--max-ralph-iterations',
        type=int,
        default=5,
        help='Max Ralph Wiggum iterations per task (default: 5)'
    )
    parser.add_argument(
        '--completion-promise',
        type=str,
        default='TASK_COMPLETE',
        help='String that indicates task completion (default: TASK_COMPLETE)'
    )

    args = parser.parse_args()

    # Validate vault path
    vault = Path(args.vault_path)
    if not vault.exists():
        print(f"Error: Vault path does not exist: {args.vault_path}")
        sys.exit(1)

    # Create orchestrator
    orchestrator = Orchestrator(
        str(vault),
        check_interval=args.interval,
        dry_run=args.dry_run,
        use_ralph_wiggum=not args.no_ralph_wiggum,
        max_ralph_iterations=args.max_ralph_iterations,
        completion_promise=args.completion_promise
    )
    
    if args.once:
        # Test mode: run once and exit
        print("Running in test mode (once)...")
        pending = orchestrator.get_pending_items()
        print(f"Found {len(pending)} pending item(s)")
        if pending:
            success, failed = orchestrator.process_items(pending)
            print(f"Processed: {success} successful, {failed} failed")
            orchestrator.update_dashboard(len(pending), success, failed)
    else:
        # Normal mode: run continuously
        orchestrator.run()


if __name__ == '__main__':
    main()
