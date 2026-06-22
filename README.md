# ai-studio-chat2html

A lightweight CLI tool that transforms Google AI Studio chat exports into clean, responsive HTML. Supports Gemini thinking blocks, Markdown rendering, and full chat metadata — all in a single-file Python script with zero external dependencies.

## Features

- 🧠 **Gemini Thinking Blocks** — rendered as collapsible sections
- 📝 **Markdown Rendering** — headings, lists, bold, code, blockquotes, and more
- ⚙️ **Run Settings** — model, temperature, top-p, and other parameters displayed
- 📱 **Responsive Design** — works on desktop and mobile
- 🪶 **Zero Dependencies** — Python stdlib only
- 🖥️ **Simple CLI** — single command, one argument

## Usage

```bash
# Basic: converts sample.json → sample.html
python3 chat2html.py sample.json

# Custom output path
python3 chat2html.py chat.json -o output.html
```

## Input Format

The tool expects a Google AI Studio chat export JSON file with the following structure:

```json
{
  "runSettings": { "model": "...", "temperature": 1.0, ... },
  "systemInstruction": {},
  "chunkedPrompt": {
    "chunks": [
      { "text": "...", "role": "user", "tokenCount": 33, "createTime": "..." },
      { "text": "...", "role": "model", "isThought": true, "tokenCount": 503, ... },
      { "text": "...", "role": "model", "finishReason": "STOP", "tokenCount": 996, ... }
    ]
  }
}
```

## Requirements

- Python 3.8+

## License

MIT
