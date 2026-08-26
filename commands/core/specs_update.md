---
name: specs_update
description: Report whether the installed project-specs framework is out of date, and upgrade it to a newer release
model: quick
---

# Specs Update

You are tasked with reporting whether the project-specs framework installed in
this project is behind the source it came from, and applying the update when the
user asks for it.

This is a mechanical command. It runs two things and reads their output. It does
not edit code, and it never resolves a conflict on the user's behalf.

## Setup (read before proceeding)

1. Find the install record at the project root: `.project-specs.json`. If it is
   absent, this project either has no framework install or has one made before
   records existed. Say so and stop; running an update writes the first record.
2. Read `source`, `ref`, `commit`, and `pinned` from the record so you can
   describe the install in the user's terms.
3. Locate the installer. The record's `source` says where the framework comes
   from; the installer itself is whichever `setup.sh` the user runs. If no local
   copy is available, the user can run any copy of `setup.sh` against this
   project — the update fetches its own source.

## Reporting

Run the staleness check:

```
<path-to>/setup.sh <project-root> --check
```

Report what it says in plain language:

- **Current** — say so in one line and stop. Nothing to do.
- **Behind by N** — say how far behind, and summarize the change-log entries the
  check printed. Lead with what changed for this user, not the revision count.
- **Pinned** — say the install is held at its pinned reference on purpose, name
  the newer revision available, and ask whether they want to move.

The check exits non-zero when a newer revision exists. That is information, not
a failure; do not report it as an error.

## Applying

Only after the user asks for the update:

```
<path-to>/setup.sh <project-root> --update
```

Then report two things:

1. Which revision the install moved to.
2. Every file the installer listed under "Kept your local changes". These are
   files the user edited, so the update left them at their edited content. If a
   kept file also changed upstream, say so — the user now has an old version of
   a file that moved, and only they can decide what to do about it.

To move a pinned install, or to change which reference a project follows, add
`--ref=<branch|tag|revision>`.

## Key Behaviors

- **Never update without being asked.** Report first. The user decides.
- **Never resolve a kept file.** Name it and hand the decision back.
- **Do not describe a non-zero exit from `--check` as a failure.** It means a
  newer revision exists.
- **Do not touch project code.** This command manages the framework install and
  nothing else.

## Red Flags

Observable signs that you are drifting off this workflow:

- You ran the update before the user asked for it
- You are editing a file the installer reported as kept
- You reported "the check failed" when the check reported an available update
- You are reading the framework's own source to decide what changed, instead of
  reporting what the check printed
