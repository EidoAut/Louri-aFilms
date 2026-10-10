# Current verification

The authoritative results and limitations for 0.3.1 are in [AUDIT-0.3.1.md](AUDIT-0.3.1.md). Older architecture reports describe their corresponding historical versions and do not override the current playback flow.

Automated checks: pytest; real QML captures via scripts/verify_ui.py; real native controls via scripts/verify_controls.py; public video/audio decoding via scripts/verify_buffered_player.py; isolated packaged startup and native playback via scripts/verify_executable.py.

These checks do not establish complete film playback, regional availability, speaker output, Windows 10 compatibility or Linux compatibility.
