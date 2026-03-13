# Example: feature workflow

## Task
Add bulk archive support to the notifications center.

## Recommended mode
Full workflow

## Intake
- Goal: allow selecting multiple notifications and archiving them at once.
- Success: UI state, optimistic updates, and rollback on error all work.
- Constraints: preserve existing single-item archive behavior.

## Explore
Inspect:
- notification list state management
- archive mutation flow
- optimistic update helpers
- API client / backend contract
- tests covering single archive action

## Plan
- add selection state
- add bulk archive action
- extend API client if needed
- add optimistic state handling
- cover success and failure paths in tests

## Verify
- targeted tests for reducer/store state
- component tests for selection and bulk action
- integration or e2e checks if available
- lint / typecheck / build

## Review focus
- partial failure handling
- stale selection after refresh
- accessibility of bulk action controls
