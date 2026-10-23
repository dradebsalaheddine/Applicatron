# The Applicatron 3000

An unnecessarily powerful name for a calmer job search.

A local-first desktop application tracker with a forest-green sidebar, a clean list view, a status board, and a follow-up radar. Built with Electron and plain HTML, CSS and JavaScript, with AI assistance.

## Windows: run it

Extract the entire Windows ZIP into a folder, then open `Applicatron3000.exe`. Keep its supporting files beside it. This is a portable application folder, not a single-file installer. It includes its own Electron runtime: Edge, WebView2, Node.js and Docker are not required on the user's machine. Opening an application link uses your default browser.

The build is unsigned. Windows launch and native save dialogs still need testing on a Windows machine; the browser interface and automated logic tests have been checked.

## Features

- Applications grouped by status and sorted by initial application date, oldest first.
- List and board views; search and status/timing filters.
- Optional consideration window: calendar-day duration or explicit end date.
- Current local date, time remaining, expired windows, and scheduled follow-ups.
- An expired window never automatically marks an application rejected.
- Edit, delete with immediate undo, JSON backup/import, and PDF export.
- Empty first launch, with an optional five-entry fictional demo.

## Your data

No account, analytics, cloud sync or app API calls. Entries are stored locally in the app's Chromium profile (`localStorage`). Data is not encrypted by this app. On Windows, the default profile is under `%APPDATA%/Applicatron 3000`; moving the application folder does not move that profile. Export backups regularly and keep them private.

To move from an earlier tracker, export its JSON backup and import it here. Import replaces the current list after confirmation. Your private backup belongs on your device, never in this repository. A fresh public build contains no real applications, CVs, contact details or user profile.

The desktop renderer is sandboxed with Node integration disabled, context isolation enabled, a strict content security policy, a bundled-asset allowlist, and HTTP(S)-only external links requiring confirmation. These controls are not a security certification.

## Develop

Use Node.js 22 or newer and npm:

```sh
npm ci
npm test
npm start
```

Build the Windows x64 portable folder:

```sh
npm run package:win
```

Output: `build/Applicatron3000-win32-x64/`. Zip the entire folder to distribute. The GitHub Actions workflow also builds it on Windows. Electron supports other desktop platforms, but this release only supplies Windows x64 packaging.

The browser-only UI can be served from `web/` with a local static server. It uses browser print for PDF; the desktop app uses a native save dialog. Browser and desktop profiles are separate.

## Validation and limits

`npm test` covers date boundaries, leap dates, status/window semantics, import validation, duplicate IDs, external URL checks and the desktop asset allowlist. Manual browser checks cover the empty screen, demo, editing, persistence, deletion/undo, board and filters. No automated Windows end-to-end test has been performed. There are no background notifications, automatic job scraping or automatic updates.

MIT licensed. Contributions welcome. Please use fictional data in issues and screenshots.
