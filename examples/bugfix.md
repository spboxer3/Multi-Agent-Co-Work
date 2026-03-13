# Example: bugfix workflow

## Task
Fix a bug where the settings panel closes when pressing Escape inside a nested modal.

## Recommended mode
Full workflow

## Intake
- Goal: keep the parent settings panel open when Escape is handled by the nested modal.
- Success: nested modal closes without collapsing the parent overlay.
- Constraints: do not regress global keyboard shortcuts.

## Explore
Look for:
- modal keydown handlers
- escape key propagation
- overlay dismissal logic
- tests around nested dialogs

## Plan
Likely edits:
- nested modal keyboard handling
- parent overlay close guard
- regression test for nested Escape behavior

## Verify
Run:
- targeted modal test
- relevant keyboard interaction suite
- lint / typecheck if applicable

## Review focus
- event propagation
- focus trap behavior
- accessibility regressions
