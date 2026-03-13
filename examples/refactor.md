# Example: refactor workflow

## Task
Refactor duplicated date formatting logic used by invoices, subscriptions, and billing history.

## Recommended mode
Standard workflow

## Explore
Find:
- all formatting utilities
- timezone assumptions
- locale defaults
- snapshot or unit tests touching date rendering

## Plan
- extract shared formatter into a single utility
- update call sites gradually
- keep old interface temporarily if needed for compatibility

## Verify
- targeted unit tests for formatting cases
- affected component tests
- lint / typecheck / build

## Review focus
- locale regressions
- timezone edge cases
- accidental API churn
