---
title: Untrack Private Runtime Files, Do Not Only Ignore Them
date: 2026-08-26
category: security-issues
module: repository_configuration
problem_type: security_issue
component: development_workflow
symptoms:
  - Earlier repository trees tracked path names intended for local settings and key material.
  - A personal vocabulary file remained tracked until a separate follow-up remediation.
  - Ignore patterns did not retroactively remove already tracked files or erase earlier Git history.
root_cause: missing_workflow_step
resolution_type: config_change
severity: high
tags: [gitignore, tracked-private-data, secret-remediation, git-index, repository-hygiene, personal-lexicon, runtime-files, history-exposure]
---

# Untrack Private Runtime Files, Do Not Only Ignore Them

## Problem

MoneyPenny's private runtime files had already entered Git's tracked history. Adding their names to `.gitignore` could prevent future accidental additions, but it could not retroactively remove paths from the index/current tree or erase earlier commits. This mattered because project documentation identifies settings as API-key-bearing and vocabulary, corrections, and transcript history as user-specific data (`QuickStart-CheatSheet.md:49-55`).

This investigation used only commit metadata, tree path names, ignore-rule provenance, and public documentation. It did not open, quote, or inspect any private runtime file.

## Symptoms

- Name-only inspection of the parent tree for `93da523` returns `settings.json` and `encryption.key`; the commit tree no longer contains those names.
- Name-only inspection of the parent tree for `dd89a29` returns `lexicon.txt`; the commit tree no longer contains it and adds `lexicon.example.txt`.
- Current `git ls-files -- settings.json encryption.key lexicon.txt corrections.json transcript_history.jsonl` returns no paths.
- Current `git check-ignore -v` maps those live names to `.gitignore:42`, `.gitignore:54`, `.gitignore:45`, `.gitignore:48`, and `.gitignore:51`, respectively.
- Safe starter artifacts remain tracked under separate example names (`README.md:91-105`).

These checks establish current tracked and ignored state. They do not prove historical blobs were purged from every ref, clone, cache, or fork, and they do not prove credential rotation.

## What Didn't Work

- Adding `.gitignore` after commit was not a tracked-state repair. Ignore rules affect discovery of untracked paths; they do not remove an indexed path.
- Deleting a private path from the current tree without an ignore rule was incomplete because the application could regenerate and later restage it.
- Keeping a tracked template under the live runtime filename would let normal application use modify a tracked file. The repaired layout uses separately named examples while the live files remain local (`README.md:76-105`).
- Checking only untracked files or the working tree was insufficient; the tracked-file set had to be inspected directly (session history).
- Removing a path from `HEAD` could not be equated with erasing history or invalidating credentials. Those are separate remediation boundaries.

## Solution

### 1. Remove live private paths from tracked trees

Commit `93da523` removes `settings.json` and `encryption.key`; commit `dd89a29` removes `lexicon.txt`. Current negative `git ls-files` output confirms those removals remain effective and that `corrections.json` and `transcript_history.jsonl` are also untracked.

Use a content-free path check:

```powershell
git ls-files -- settings.json encryption.key lexicon.txt corrections.json transcript_history.jsonl
```

Expected result: no output.

### 2. Ignore every live runtime-data path

The current `.gitignore` separately covers settings, personal vocabulary, exact corrections, captured transcript history, and the legacy encryption key (`.gitignore:41-54`). `git check-ignore -v` verifies both the decision and the supplying rule.

### 3. Track safe examples under distinct names

The repository tracks `lexicon.example.txt` and `corrections.example.json`, not the live user files. The README presents them as safe starters and labels the live files private/local (`README.md:76-105`). This preserves onboarding material without versioning user state.

### 4. Keep rotation and history remediation explicit

Untracking and ignoring prevent ordinary future commits under those paths; they do not invalidate any credential that appeared earlier or erase historical objects. Provider-side revocation/rotation and any coordinated history rewrite are separate operations. Project notes report key rotation, but this capture did not independently verify it and therefore does not mark it complete.

## Why This Works

The negative `git ls-files` result verifies the current index/tree side of the repair. `git check-ignore -v` verifies the prevention side for regenerated local files. Both are required because either one alone is incomplete.

Separately named examples avoid a tracked/untracked identity collision. Git versions generic setup guidance while the application reads and writes distinct live filenames (`README.md:76-105`).

Name-only earlier-tree inspection safely proves the historical tracked-state transition without reopening sensitive blobs. The parent trees contain the affected names while the current index does not.

Keeping four statuses separate prevents security overclaims:

- ignored now;
- untracked now;
- purged from history or not;
- credential invalidated or not.

## Prevention

Add a content-free tracked-path gate to release and security checks:

```powershell
$privatePaths = @(
    'settings.json',
    'encryption.key',
    'lexicon.txt',
    'corrections.json',
    'transcript_history.jsonl'
)
git ls-files -- $privatePaths
git check-ignore -v -- $privatePaths
```

The first command must return no paths; the second must resolve every live name to the intended rule (`.gitignore:41-54`). Neither command reads contents.

- Keep public templates under unmistakable `.example` names and build them from reviewed placeholders, never by copying a live user file.
- When adding runtime-data features, define the live filename, ignore rule, and—only if onboarding needs it—a separate safe example before release.
- Stage release files explicitly and inspect both `git status` and `git ls-files`; do not use `.gitignore` as proof of current tracked state (session history).
- If a secret-bearing path is found tracked, report current untracking, ignore coverage, history remediation, and provider-side rotation as separate verified statuses.
- Do not mark rotation complete from a project note alone; require authoritative provider-side evidence and never record credential values.

## Related Issues

- [LESSONS_LEARNED.md](../../../LESSONS_LEARNED.md) contains the original incident narrative and rotation report; rotation remains unverified in this capture.
- [DECISIONS.md](../../../DECISIONS.md) records the project decision that settings and vocabulary are local user data.
- [SESSION_CLOSEOUT.md](../../../SESSION_CLOSEOUT.md) is the current recurring tracked-file safety gate.
- [ROADMAP.md](../../../ROADMAP.md) retains the unresolved defense-in-depth move from plaintext settings to Windows credential storage.
- [deterministic-exact-transcript-corrections.md](../logic-errors/deterministic-exact-transcript-corrections.md) shows the live-file/example-file pattern for correction rules.
