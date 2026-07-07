# Architecture — VinylSplit for Audacity v0.1

## Overview

VinylSplit for Audacity is a desktop wizard application that guides users through digitizing vinyl recordings in Audacity. Version 0.1 establishes project structure, core infrastructure, and a placeholder seven-step wizard.

## Layers

```
┌─────────────────────────────────────────┐
│  app.py — bootstrap & event loop        │
├─────────────────────────────────────────┤
│  wizard/ — QWizard workflow & pages     │
├─────────────────────────────────────────┤
│  ui/ + resources/ — Qt Designer assets  │
├─────────────────────────────────────────┤
│  Domain packages (stubs in v0.1)        │
│  musicbrainz · metadata · labels        │
│  audacity · export                      │
├─────────────────────────────────────────┤
│  core/ — logging · settings · DI        │
└─────────────────────────────────────────┘
```

## Core Infrastructure

### Logging (`core/logging_config.py`)

Configures console and rotating file handlers. Log files are stored in a platform-specific user directory.

### Settings (`core/settings.py`)

Wraps `QSettings` with typed key constants. Wizard pages persist lightweight state (e.g. last artist/album search).

### Dependency Injection (`core/container.py`)

A minimal service locator registers lazy singletons. Future clients (MusicBrainz, Audacity) register factories here rather than being constructed inside UI code.

## Wizard

`VinylSplitWizard` registers seven pages by stable `PageId` enum values. Each page subclasses `WizardPageBase`, receives the `Container`, and overrides `build_content()`.

Pages are Qt Designer compatible via `WizardPageBase.load_ui()`.

## Planned Integration Points

| Package       | Responsibility                          | v0.1 Status |
|---------------|-----------------------------------------|-------------|
| `musicbrainz` | Release search and track metadata       | Stub        |
| `metadata`    | Domain models and session state         | Stub        |
| `labels`      | Label position calculation              | Stub        |
| `audacity`    | Project and label track bridge          | Stub        |
| `export`      | Split-and-export orchestration          | Stub        |

## Extension Guidelines

1. Add domain logic in packages, not wizard pages.
2. Register new services in `Container._register_defaults()`.
3. Share session state via a future `metadata.WizardSession` resolved from the container.
4. Keep `.ui` files in `ui/`; load from page subclasses.