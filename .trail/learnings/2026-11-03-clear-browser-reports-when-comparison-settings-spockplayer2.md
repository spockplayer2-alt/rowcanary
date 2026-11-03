---
title: Clear browser reports when comparison settings change
author: Spockplayer2
date: 2026-11-03
branch: main
id: l-b94e549f
scope: repo
status: active
src: agent
touches:
  - CHANGELOG.md
  - MANIFEST.in
  - PROGRESS.md
  - README.md
  - docs/development-plan.md
  - docs/quickstart.md
  - docs/release-notes.md
  - docs/screenshots/desktop.png
  - docs/screenshots/mobile-dark.png
  - docs/verification.md
---

## Decided
Clear the current report on mode or input changes and lock fields while a request runs. A PASS describes only the inputs used for that request.
## Tried and ruled out
Keeping the previous result visible after returning to generation left a stale PASS on screen. Actual Edge reproduced it before the change and passed afterward.
## Watch out
Retain focus on completed results and announce errors. Test both mode changes and a replacement upload.
In the code: rowcanary/static/app.js clearReport/setMode; browser evidence in docs/verification.md.
