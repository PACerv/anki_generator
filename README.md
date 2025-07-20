# Anki Card Creator

An intelligent study card generator that uses Google's Gemini AI to extract information from images and PDFs to create Anki-compatible flashcards.

## Features

- 📷 Upload images containing text (documents, notes, screenshots)
- 📄 Upload PDF files (textbooks, papers, lecture notes)
- 🤖 AI-powered text extraction using Gemini Vision and Document AI
- 📚 Custom study material generation based on your learning goals
- 🎯 Anki-compatible deck export (.apkg format)
- 🎨 Beautiful Gradio web interface

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up your Google API key:
   - Get a Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create a `.env` file with your API key:
```
GOOGLE_API_KEY=your_api_key_here
```

3. Run the application:
```bash
python app.py
```

## Usage

1. Upload an image or PDF containing text you want to study
2. Describe what kind of study materials you want (e.g., "vocabulary words", "historical facts", "math formulas")
3. Let the AI extract information and generate study cards
4. Download the generated Anki deck (.apkg file)
5. Import into Anki for studying

## Requirements

- Python 3.8+
- Google Gemini API key
- Anki (for importing the generated decks)

## Supported File Types

- **Images**: JPEG, PNG, GIF, BMP, TIFF, WebP
  - Handwritten notes
  - Screenshots of presentations
  - Scanned documents
  - Whiteboard photos

- **PDFs**: Text-based and scanned PDFs
  - Research papers
  - Textbooks
  - Lecture notes
  - Study guides
