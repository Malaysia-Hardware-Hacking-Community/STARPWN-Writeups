---
title: "Follow_The_Leak"
ctf: "STARPWN 2026 (DEF CON / Aerospace Village)"
date: 2026-08-09
category: "Forensics"
points: 500
flag_format: "flag{...}"
author: "gluppler"
---

# Follow_The_Leak

## Summary

A 640 MB ZIP archive (`opensatkit-badpush-student.zip`) containing a student satellite development repository was provided. The challenge description said: "Incidence response believes that the point of entry originated from information somewhere within this archive." The flag was accidentally committed to a COSMOS configuration file in Git history, then "scrubbed" from the main branch — but Git history retains it.

## What is OpenSatKit / COSMOS?

- **OpenSatKit (OSK)**: An open-source satellite flight software framework based on NASA cFS (core Flight System)
- **COSMOS (Command and Data System)**: A ground station software suite for satellite command & control, telemetry processing, and visualization
- The repository is a full OSK workspace with cFS apps, COSMOS configs, mission definitions, and 42 simulator integration

## Investigation

### Step 1: Unzip and Explore

```bash
unzip opensatkit-badpush-student.zip
# Creates student/ directory with 42/, cfs/, cosmos/, docs/, etc.
```

The repository is a full satellite development environment. The challenge hint: "point of entry originated from information somewhere within this archive" — meaning a secret (credential, key, flag) was left in the codebase.

### Step 2: Search for Flags/Secrets in Current Files

```bash
grep -r "STARPWN{" student/
grep -r "flag{" student/
grep -r "CDS_KEY" student/
# No hits in current working tree
```

The secrets aren't in the current snapshot — they were removed ("scrubbed") but Git history keeps them.

### Step 3: Check Git History

The `student/` directory is a Git repository (there's a `.git` folder). Let's examine the commit history:

```bash
cd student
git log --oneline -20
```

Key commits:
- `6d7902d5` "remove large binaries" — recent cleanup
- `035b9b27` "docs: incident report for credential scrub (history rewrite)" — **this is the smoking gun**
- `9967456c` "cosmos:temp lab key" — added a temporary lab key
- `260db5f9` "cosmos:temp lab key" — another key commit

### Step 4: Examine the "Credential Scrub" Commit

```bash
git show 035b9b27
```

This shows an incident report was added documenting that "a mission credential was accidentally committed to a COSMOS key file during lab bring-up" and "repository history was rewritten to remove the credential."

### Step 5: Find the Actual Credential Commit

The commit that *added* the key (before it was scrubbed):

```bash
git show 9967456c
```

Output:
```diff
+ # NOTE: TEMPORARY — remove before flight
+ CDS_KEY=ZmxhZ3s1MHJyeV9XMTVoX1czX0MwdWxkX0cwXzcwXzdoM19NMDBuXzcwZzM3aDNyfQ==
```

There it is! A base64-encoded string in a COSMOS key file (`.cdskeyfile`).

### Step 6: Decode the Flag

```bash
echo "ZmxhZ3s1MHJyeV9XMTVoX1czX0MwdWxkX0cwXzcwXzdoM19NMDBuXzcwZzM3aDNyfQ==" | base64 -d
```

Output:
```
flag{50rry_W15h_W3_C0uld_G0_70_7h3_M00n_70g37h3r}
```

## Why This Works

1. **Git never forgets**: Even after history rewriting (`git filter-branch`, `git rebase -i`, BFG Repo-Cleaner), the old objects remain in the repository until garbage collection (`git gc --prune=now`) runs. The challenge repo hadn't been GC'd.

2. **Secrets in config files**: COSMOS uses `.cdskeyfile` for encryption keys. Developers sometimes commit these by accident during lab bring-up.

3. **Incident reports leak meta-info**: The commit message "credential scrub (history rewrite)" explicitly tells you a secret was removed — that's your cue to dig into history.

## Lessons Learned

- **Always scan Git history for secrets**, not just the working tree. Tools: `git log --all --full-history -- <path>`, `truffleHog`, `gitleaks`, `git-secrets`.
- **"History rewriting" ≠ deletion**: The objects persist until `git gc --prune=now` physically removes unreachable objects. Most repos don't run this aggressively.
- **Base64 is not encryption**: The key was base64-encoded, not encrypted. Anyone with repo access can decode it.
- **Pre-commit hooks are essential**: A `gitleaks` or `git-secrets` pre-commit hook would have caught this before commit.

## Complete Reproduction

```bash
cd student
# Find commits touching cosmos key files
git log --all --full-history -- cosmos/.cdskeyfile

# Show the commit that added the key
git show 9967456c66dba0ef2df2a86c263f14145afad596

# Decode
echo "ZmxhZ3s1MHJyeV9XMTVoX1czX0MwdWxkX0cwXzcwXzdoM19NMDBuXzcwZzM3aDNyfQ==" | base64 -d
# flag{50rry_W15h_W3_C0uld_G0_70_7h3_M00n_70g37h3r}
```

## Flag

```
flag{50rry_W15h_W3_C0uld_G0_70_7h3_M00n_70g37h3r}
```