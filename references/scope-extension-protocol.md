# Scope extension protocol

Use this only in implement.

## Trigger
The implementer must request scope extension when any of these happen:
- a locked file has an unlisted shared consumer
- a required test file is outside the locked file set
- a missing prerequisite blocks a safe patch
- the planned edit would create inconsistent behavior unless one more file changes

## Required output
Return all of the following:
- `scope_extension_needed=true`
- `scope_extension_reason`
- `requested_files`
- `rollback_anchor`
- `decision="request-scope-extension"`

## What not to do
Do not silently patch the extra file.
Do not hide the extra file inside `notes`.
Do not downgrade the need to a “risk” just to keep moving.

## Planner response
The planner must either:
- approve the file-set change and relock the plan, or
- reject the extension and require a different patch strategy
