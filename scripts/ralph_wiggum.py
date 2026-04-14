"""
Ralph Wiggum Loop Implementation

Implements the "Ralph Wiggum" persistence pattern for multi-step task completion.
This Stop hook pattern keeps Qwen Code working until tasks are complete.

Usage:
    python scripts/ralph_wiggum.py "Process all files in Needs_Action" --vault AI_Employee_Vault
    python scripts/ralph_wiggum.py "Generate invoices for pending requests" --max-iterations 10

Reference: https://github.com/anthropics/claude-code/tree/main/.claude/plugins/ralph-wiggum
"""

import os
import sys
import subprocess
import argparse
import logging
import time
from typing import Optional, Tuple
from pathlib import Path
from datetime import datetime

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class RalphWiggumLoop:
    """
    Ralph Wiggum Loop for persistent task completion.
    
    How it works:
    1. Orchestrator creates state file with prompt
    2. Qwen Code works on task
    3. Qwen Code tries to exit
    4. Stop hook checks: Is task file in /Done?
    5. YES → Allow exit (complete)
    6. NO → Block exit, re-inject prompt (loop continues)
    7. Repeat until complete or max iterations
    """
    
    def __init__(
        self,
        vault_path: str = 'AI_Employee_Vault',
        max_iterations: int = 10,
        completion_promise: str = None,
        dry_run: bool = False
    ):
        """
        Initialize Ralph Wiggum Loop.
        
        Args:
            vault_path: Path to Obsidian vault
            max_iterations: Maximum loop iterations
            completion_promise: String that indicates completion
            dry_run: If True, log actions without executing
        """
        self.vault_path = Path(vault_path)
        self.max_iterations = max_iterations
        self.completion_promise = completion_promise or 'TASK_COMPLETE'
        self.dry_run = dry_run
        
        # Define folders
        self.needs_action = self.vault_path / 'Needs_Action'
        self.done = self.vault_path / 'Done'
        self.plans = self.vault_path / 'Plans'
        self.pending_approval = self.vault_path / 'Pending_Approval'
        self.logs = self.vault_path / 'Logs'
        
        # State tracking
        self.current_iteration = 0
        self.task_complete = False
        
        # Setup logging
        self._setup_logging()
        
        self.logger.info(f'Initialized RalphWiggumLoop')
        self.logger.info(f'Vault: {self.vault_path}')
        self.logger.info(f'Max iterations: {self.max_iterations}')
    
    def _setup_logging(self):
        """Setup logging."""
        log_dir = self.logs
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / f'ralph_wiggum_{datetime.now().strftime("%Y-%m-%d")}.log'
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ],
            encoding='utf-8'
        )
        self.logger = logging.getLogger('RalphWiggumLoop')
    
    def check_completion(self, prompt: str) -> Tuple[bool, str]:
        """
        Check if task is complete using multiple strategies.
        
        Strategies:
        1. Completion promise in output
        2. File movement to /Done
        3. No more items in /Needs_Action
        
        Args:
            prompt: Original prompt
            
        Returns:
            Tuple of (is_complete, reason)
        """
        # Strategy 1: Check for completion promise
        # This would be checked in Qwen's output
        # For now, we check if it was explicitly marked
        
        # Strategy 2: Check if files moved to /Done
        needs_action_count = len(list(self.needs_action.glob('*.md')))
        
        if needs_action_count == 0:
            self.logger.info('✓ No items in Needs_Action - task complete')
            return (True, 'All items processed')
        
        # Strategy 3: Check if pending approvals exist (waiting for human)
        pending_count = len(list(self.pending_approval.glob('*.md')))
        
        if pending_count > 0 and needs_action_count == 0:
            self.logger.info(f'✓ Waiting for human approval ({pending_count} items)')
            return (True, f'Waiting for approval: {pending_count} items')
        
        # Task not complete
        self.logger.info(f'✗ Task not complete: {needs_action_count} items pending')
        return (False, f'{needs_action_count} items remaining')
    
    def run_qwen_code(self, prompt: str, iteration: int) -> str:
        """
        Run Qwen Code with the given prompt.
        
        Args:
            prompt: The prompt to send
            iteration: Current iteration number
            
        Returns:
            Qwen Code output
        """
        self.logger.info(f'Running Qwen Code (iteration {iteration + 1}/{self.max_iterations})')
        
        if self.dry_run:
            self.logger.info(f'[DRY RUN] Would run Qwen Code with prompt')
            return ''
        
        # Build enhanced prompt with Ralph Wiggum instructions
        enhanced_prompt = self._build_ralph_prompt(prompt, iteration)
        
        # Change to vault directory
        cwd = str(self.vault_path)
        
        try:
            # Run Qwen Code
            # Using --yolo mode for autonomous operation
            cmd = f'echo "{enhanced_prompt}" | qwen --yolo'
            
            result = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                shell=True,
                encoding='utf-8',
                errors='replace'
            )
            
            output = result.stdout + result.stderr
            
            # Log output
            self.logger.info(f'Qwen Code output length: {len(output)} chars')
            
            return output
            
        except subprocess.TimeoutExpired:
            self.logger.error('Qwen Code timed out')
            return ''
        except FileNotFoundError:
            self.logger.error('Qwen Code not found. Please ensure it is installed and in PATH.')
            return ''
        except Exception as e:
            self.logger.error(f'Error running Qwen Code: {e}')
            return ''
    
    def _build_ralph_prompt(self, base_prompt: str, iteration: int) -> str:
        """
        Build enhanced prompt with Ralph Wiggum instructions.
        
        Args:
            base_prompt: Original task prompt
            iteration: Current iteration
            
        Returns:
            Enhanced prompt
        """
        ralph_instructions = f"""
## IMPORTANT: Task Persistence Mode (Ralph Wiggum Pattern)

You are in **Task Persistence Mode**. This means:

1. **DO NOT exit** until the task is fully complete
2. **Keep working** through multiple steps if needed
3. **Move files to /Done** when you finish processing them
4. **Output "{self.completion_promise}"** when the entire task is complete

### Current Task

{base_prompt}

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

### Iteration {iteration + 1}

This is iteration {iteration + 1} of {self.max_iterations}.

If there are still items in /Needs_Action, **keep working**.
If you are waiting for approval, **stop and wait**.
If all items are processed, **output "{self.completion_promise}"**.

Begin processing now.
"""
        
        return ralph_instructions
    
    def run(self, prompt: str) -> bool:
        """
        Run the Ralph Wiggum Loop.
        
        Args:
            prompt: Task prompt
            
        Returns:
            True if task completed successfully
        """
        self.logger.info(f'Starting Ralph Wiggum Loop')
        self.logger.info(f'Task: {prompt[:100]}...')
        
        print(f"\n{'='*60}")
        print(f"RALPH WIGGUM LOOP - Task Persistence Mode")
        print(f"{'='*60}")
        print(f"Task: {prompt[:80]}...")
        print(f"Max iterations: {self.max_iterations}")
        print(f"Completion signal: {self.completion_promise}")
        print(f"{'='*60}\n")
        
        for iteration in range(self.max_iterations):
            self.current_iteration = iteration + 1
            
            print(f"\n[Iteration {self.current_iteration}/{self.max_iterations}]")
            
            # Check completion before running
            is_complete, reason = self.check_completion(prompt)
            
            if is_complete:
                print(f"\n[OK] Task complete: {reason}")
                self.task_complete = True
                self.logger.info(f'Task completed: {reason}')
                return True
            
            # Run Qwen Code
            print(f"[Running Qwen Code...]\n")
            output = self.run_qwen_code(prompt, iteration)
            
            # Check for completion promise in output
            if self.completion_promise in output:
                print(f"\n[OK] Completion promise detected")
                self.task_complete = True
                self.logger.info('Completion promise detected in output')
                return True
            
            # Check completion after running
            is_complete, reason = self.check_completion(prompt)
            
            if is_complete:
                print(f"\n[OK] Task complete: {reason}")
                self.task_complete = True
                return True
            
            # Log iteration
            self.logger.info(f'Iteration {iteration + 1} complete, continuing...')
            
            # Small delay before next iteration
            time.sleep(2)
        
        # Max iterations reached
        self.logger.warning(f'Max iterations ({self.max_iterations}) reached')
        print(f"\n{'='*60}")
        print(f"[WARN] Max iterations reached")
        print(f"Task may not be fully complete")
        print(f"{'='*60}\n")
        
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Ralph Wiggum Loop for persistent task completion'
    )
    parser.add_argument(
        'prompt',
        type=str,
        help='Task prompt (what Qwen should do)'
    )
    parser.add_argument(
        '--vault',
        type=str,
        default='AI_Employee_Vault',
        help='Path to Obsidian vault (default: AI_Employee_Vault)'
    )
    parser.add_argument(
        '--max-iterations',
        type=int,
        default=10,
        help='Maximum loop iterations (default: 10)'
    )
    parser.add_argument(
        '--completion-promise',
        type=str,
        default='TASK_COMPLETE',
        help='String that indicates task completion (default: TASK_COMPLETE)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Log actions without executing (for testing)'
    )
    
    args = parser.parse_args()
    
    # Validate vault path
    vault = Path(args.vault)
    if not vault.exists():
        print(f"[ERROR] Vault path does not exist: {vault}")
        sys.exit(1)
    
    # Create and run loop
    loop = RalphWiggumLoop(
        vault_path=str(vault),
        max_iterations=args.max_iterations,
        completion_promise=args.completion_promise,
        dry_run=args.dry_run
    )
    
    success = loop.run(args.prompt)
    
    if success:
        print("\n[SUCCESS] Task completed successfully!\n")
        sys.exit(0)
    else:
        print("\n[WARN] Task may not be fully complete\n")
        sys.exit(1)


if __name__ == '__main__':
    main()
