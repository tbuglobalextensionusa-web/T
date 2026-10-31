# T

## Edge TTS

[edge-tts](https://github.com/rany2/edge-tts) provides text-to-speech using
Microsoft Edge's online service. No API key is required.

### Install

Requires Python 3.8+ with `venv` and `pip` available.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

### Use

```bash
# Check the installation
.venv/bin/edge-tts --version

# List available voices (requires internet access)
.venv/bin/edge-tts --list-voices

# Generate an MP3
mkdir -p output
.venv/bin/edge-tts --text "Hello! Welcome to T." --write-media output/hello.mp3
```

Use `--voice VOICE_NAME` to select a voice, or `--file script.txt` instead of
`--text` to read text from a file. Run `.venv/bin/edge-tts --help` for all options.

Speech generation and voice listing require access to Microsoft's online
endpoints. This Arena sandbox restricts outbound network access and does not
allow those endpoints, so installation and local CLI checks work here, but
online synthesis must run in an environment that permits that access.

The virtual environment and generated files in `output/` are not tracked in Git.
Re-run the installation commands if the environment is recreated.
