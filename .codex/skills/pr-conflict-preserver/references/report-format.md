# Report Format

`summary.json` is the authoritative machine-readable output of the skill's script.

## Top-Level Keys

- `mode`: `pr-vs-base`, `pr-vs-pr`, or `branch-vs-branch`
- `repo_root`: absolute repository root
- `worktree_path`: isolated worktree path created for the run
- `resolution_branch`: branch created for the run
- `artifact_dir`: timestamped artifact directory inside the worktree
- `steps`: ordered merge attempts and their outcomes
- `final_status`: `committed`, `resolved`, `unresolved`, or `validation_failed`

## Per-Step Fields

- `label`: short step label such as `merge-pr-123`
- `target`: merged ref description
- `status`: `clean`, `resolved`, `unresolved`, or `validation_failed`
- `resolved_files`: files fully auto-resolved in that step
- `unresolved_files`: files that still contain unresolved hunks
- `report_path`: step-level JSON report path
- `commit`: commit SHA when the step ended in a commit

## File Artifacts

For each conflicted file, the script creates `files/<sanitized-path>/` containing:

- `base`
- `ours`
- `theirs`
- `hunks.json`

`hunks.json` stores one object per conflict hunk:

- `index`
- `status`: `resolved` or `unresolved`
- `reason`
- `base`
- `ours`
- `theirs`
- `merged_preview`

`merged_preview` is the exact text placed into the merged file for that hunk. For unresolved hunks it is diff3 marker text, not a guessed resolution.
