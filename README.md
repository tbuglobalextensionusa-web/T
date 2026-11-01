# T

## Children and Adolescent Counseling Curriculum

- [Curriculum and MCQ coverage map](docs/curriculum.md)
- [PDF book production requirements](docs/production-requirements.md)
- [Book production plan and progress register](docs/book-production-plan.md)

The curriculum contains 24 core courses, eight electives, and four integrative areas. The confirmed structure is **32 separate PDF books—one per course—with no voice or audio files**. The four integrative areas will be incorporated into relevant course books. The books are to use simple-English lecture-style writing, real-life applications, and diagrams or illustrations where appropriate. Each finished book PDF must contain at least 150,000 words, for a combined minimum of 4,800,000 words. Production follows curriculum order. **CAC.901 is complete:** [Advanced Developmental Psychology PDF](deliverables/CAC-901-advanced-developmental-psychology.pdf), 437 pages, with 153,737 conservative body-prose words verified from the PDF, excluding references and front matter. It includes new course lectures, diagrams, and exercises alongside attributed OpenStax adaptations. The remaining 31 books are pending; next is CAC.902.

## Existing Repository Utility: Edge TTS

The text-to-speech utility below was already present in this repository. It is not part of the PDF book deliverables and will not be used to produce audio for this project.

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
