# Fokus for macOS

Fokus is a standalone macOS menu bar Pomodoro application.
It is derived from KDE Plasma widget https://gitlab.com/divinae/focus-plasmoid/

The new app keeps the original timer model and settings surface:

- Focus, short break, and long break sessions
- Flowmodoro mode
- Start/end notifications
- Optional sound effects
- Script hooks for focus/break start and end
- Fullscreen break overlay

### Attention

I'm porting this because I have found no alternatives as flexible as this widget, with easily ad hoc modifiable focus (flow) and break time and configurable hooks.
The original Pomodoro raises the barrier to start the flow,
because you cannot pause, you cannot modify the flow timing if you got distracted, you cannot extend or shorten the break.
Since such an indivisible pomodoro is a challenge which requires substantial effort, accompanied by discouragement from incomplete or imprecise pomodoros,
your brain will resist starting this challenge. For some people, these drawbacks outweigh the benefits of the guardrails in the original Pomodoro method.

The key difference is changing the time by mouse scrolling, adjusting it to the actual approximate focused time, particularly after distractions.
Nevertheless, distractions should still be minimized during focus.
Also, the break time can be changed the same way if planned to be shorter or longer.
This allows easier flow start and self-directed flow control when attention is in deficit, which concerns most people, and especially those with ADHD.

### Self-tracking

It's convenient to describe what is done after every focus, to complete the time tracking which the flexible Pomodoro enables.
Since the idea relies on flexibility, plan your tasks elsewhere before starting.
The following [script](./mac_end_cycle.sh) can be set to "Start break" or "End focus" hooks to gather the focus feedback after each focus,
which is then saved in an adjacent `logs` directory by date.
The script also shows the daily summary after every focus as a small reward or vice versa.

## Requirements

- macOS
- Python 3.9+
- Apple Silicon is supported

## Run locally

[Download](https://github.com/2e3s/fokus-macos/releases) the compressed bundle and install by dragging in Finder's Applications folder.
Otherwise, pull the sources and run:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
fokus-macos
```

You can also run it directly with:

```bash
PYTHONPATH=src python -m fokus_macos
```

## Build a standalone macOS app bundle

Install the optional build dependency and run the build helper:

```bash
. .venv/bin/activate
python -m pip install -e ".[build]"
fokus-macos-build
```

This produces:

- `dist/Fokus.app` — macOS app bundle which can be installed by dragging in Finder's Applications folder.
- `dist/Fokus/Fokus` — executable inside the supported `onedir` layout

If you prefer to call PyInstaller yourself, the repository includes `fokus-macos.spec`.

## Notes about platform differences

- The menu bar item is icon-based. The old Plasma options for hiding/showing compact-view icon/time are kept in settings for compatibility, but Qt's macOS tray API does not expose the same text-in-tray behavior as the plasmoid.
- The old KDE Do Not Disturb integration does not exist on macOS. The setting is preserved, but the app does not force Focus mode itself. If you want that behavior, use the script hooks to call your own macOS automation.
- Default Linux sound paths from the plasmoid were intentionally not carried over. On macOS, choose your own audio files in Settings. Some system sounds may be found at `/System/Library/Sounds/`.

The legacy plasmoid sources are still kept under `package/` as the reference.
