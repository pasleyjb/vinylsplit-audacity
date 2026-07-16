# Snap Store classic confinement request (draft)

Post this in the Snapcraft forum category **store-requests**:
https://forum.snapcraft.io/c/store-requests/15

---

**Title:** Classic confinement for `vinylsplit`

**Body:**

Hello,

I'd like to request classic confinement for the `vinylsplit` snap.

## Summary

VinylSplit is a desktop companion app for Audacity. It drives Audacity
through **mod-script-pipe** (named FIFOs under the host `/tmp`) to generate
album track layouts from MusicBrainz metadata and export tagged audio.

## Why classic is required

On Linux, Audacity exposes:

- `/tmp/audacity_script_pipe.to.<uid>`
- `/tmp/audacity_script_pipe.from.<uid>`

Strict snaps use a private `/tmp` mount namespace, so they cannot open the
host Audacity FIFOs. Without host `/tmp` access, VinylSplit cannot connect
to Audacity at all — that is the core function of the app.

We evaluated `system-files` write access to `/tmp`, but that still conflicts
with the snap private `/tmp` layout for FIFO open/listen semantics, and
would not auto-connect for end users. Classic confinement matches how
other host-integrated developer/audio tools are packaged.

## Interfaces / access

- Full host filesystem access is only needed to reach Audacity's
  mod-script-pipe FIFOs under `/tmp` and normal user files for export.
- Network is used for MusicBrainz lookups.
- No background daemons; user-launched GUI only.

## Publisher

- Snap name: `vinylsplit`
- Upstream: https://github.com/pasleyjb/vinylsplit-audacity
- License: MIT
- Version: 1.0.0

Thanks for reviewing.
