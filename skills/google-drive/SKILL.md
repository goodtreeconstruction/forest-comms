---
name: google-drive
description: Interact with Google Drive, including listing, reading, and writing files, and managing permissions, using rclone for robust and flexible file operations. Use when Google Drive access is needed for file management tasks.
---

# Google Drive

## Overview

This skill enables seamless interaction with Google Drive using the `rclone` command-line tool. It supports operations like listing directory contents, copying files to and from Google Drive, and synchronizing directories.

## Core Capabilities

### 1. Check Connectivity and List Contents

To verify access and list the contents of your Google Drive remote, use the `rclone ls` command. Replace `redwood:` with the actual name of your configured Google Drive remote.

```bash
rclone ls redwood:
```

### 2. Copy Files

To copy files or directories to Google Drive, use `rclone copy`.

**Copy local file to Google Drive:**
```bash
rclone copy /path/to/local/file.txt redwood:/path/on/drive/
```

**Copy file from Google Drive to local:**
```bash
rclone copy redwood:/path/on/drive/file.txt /path/to/local/
```

### 3. Synchronize Directories

To synchronize a local directory with a Google Drive directory (one-way sync from source to destination), use `rclone sync`. **Use with caution, as this can delete files at the destination that are not present at the source.**

```bash
rclone sync /path/to/local/folder redwood:/path/on/drive/folder
```

## Resources (optional)

[Remove this section, as no specific bundled scripts, references, or assets are immediately needed for this skill. The skill primarily guides the use of `rclone` via `exec`.]