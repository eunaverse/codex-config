---
name: terraform-console-drift-sync
description: Reconcile Terraform drift caused by AWS Console changes. Use when resources were modified outside Terraform and the user asks to reflect those changes into local Terraform code or state (`.tf`, `.tfvars`, import blocks), validate with `terraform plan`, and avoid accidental rollback on next apply.
---

# Terraform Console Drift Sync

## Goal

Reflect intentional console-side AWS changes into Terraform safely, then confirm Terraform and real infrastructure match.

## Workflow

1. Locate Terraform root and variable-loading method.
2. Capture drift with refresh-only plan.
3. Classify each drift item.
4. Update Terraform code (or import) only where needed.
5. Re-run plan until unintended changes disappear.
6. Sync state with refresh-only apply when requested.

## 1) Locate Terraform Root

- Find the directory containing Terraform files (`*.tf`).
- Check which var file is actually used:
  - Prefer `terraform.tfvars` for auto-loading.
  - If a custom filename is used, run commands with `-var-file=<file>` consistently.
- Run `terraform init` if the working directory has not been initialized.

## 2) Capture Drift

Run refresh-only first to inspect out-of-band changes without changing cloud resources.

```bash
terraform plan -refresh-only -out=drift.tfplan
terraform show drift.tfplan
```

## 3) Classify Drift

For each change, classify before editing:

- Computed/runtime fields:
  - Example: `latest_restorable_time`, version counters, timestamps.
  - Action: Usually no code change.
- Intentional configuration changed in console:
  - Example: retention days, ALB flags, target group health check values.
  - Action: Update `.tf`/`.tfvars` to match intended value.
- Secret value rotations:
  - Example: `aws_ssm_parameter` value/version changes.
  - Action: Keep secure pattern (`ignore_changes = [value]`) unless user explicitly wants Terraform to manage raw secret values.
- Console-created resources not in code:
  - Action: Add resource block and import (`import {}` or `terraform import`).
- Provider/service churn that should not trigger redeploy:
  - Example: frequently changing task definition revision.
  - Action: Consider `lifecycle.ignore_changes` only when this is an intentional management policy.

## 4) Apply Code Updates

- Prefer changing variables (`.tfvars`) over hard-coding constants.
- Keep edits minimal and directly traceable to drift items.
- Preserve existing behavior not related to the drift request.
- Run formatter when relevant (`terraform fmt`).

## 5) Validate

Run a normal plan and inspect carefully:

```bash
terraform plan
```

Target result:

- No changes, or
- Only user-intended changes

If plan still contains unrelated changes, resolve variable mismatch, defaults, or lifecycle policy before apply.

## 6) Optional State Sync

When code already matches infra but state is stale, sync state only:

```bash
terraform plan -refresh-only -out=drift.tfplan
terraform apply drift.tfplan
```

This records refreshed values into state without modifying remote objects.

## Safety Rules

- Do not run destructive actions without explicit user confirmation.
- Call out risky changes (`destroy`, replacements, broad policy changes) before apply.
- Distinguish clearly between code sync and state sync in the report.

## Response Template

Use this structure in the final report:

1. Drift items found
2. What was changed in code (file + key line)
3. What was intentionally not changed (and why)
4. Final `terraform plan` result
5. Next required action (if any)
