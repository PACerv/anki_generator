import os
import re
from typing import Optional, Tuple, List, Dict, Union
import gradio as gr
from PIL import Image
from dotenv import load_dotenv

from anki_gen.gemini_client import GeminiClient
from anki_gen.card_generator import AnkiCardGenerator

# Load environment variables
load_dotenv()


class AnkiCardCreatorApp:
    """Main application class for the Anki Card Creator."""

    def __init__(self):
        """Initialize the application."""
        # Initialize Gemini client with environment variable
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is required")

        self.gemini_client = GeminiClient(api_key=api_key)
        self.card_generator = AnkiCardGenerator()
        self.current_cards = []
        self.existing_cards = []  # Store cards from uploaded deck
        self.existing_deck_metadata = {}  # Store metadata from uploaded deck
        self.current_text = ""
        self.current_card_index = 0
        self.prepared_prompts = self._get_prepared_prompts()
        self.selected_cards = []  # Track which cards are selected for deck creation

        # Multi-file support
        self.source_files = []  # List of processed files with metadata
        self.all_extracted_texts = []  # All extracted texts from multiple files
        self.cards_by_source = {}  # Track which cards came from which source

    def _get_prepared_prompts(self) -> Dict[str, str]:
        """Get dictionary of prepared prompts for different learning objectives.

        Returns:
            Dictionary mapping prompt names to descriptions
        """
        return {
            "Custom (Enter your own)": "",
            "Japanese Vocabulary (Intermediate)": """Create comprehensive Japanese vocabulary cards for intermediate students using HTML formatting for better structure. IMPORTANT: Only focus on native Japanese words written in kanji and/or hiragana. Avoid katakana words (foreign loanwords), proper names, and English words.

- Front: Display the <strong>kanji/word</strong> in large, clear text. If it is a kanji word, don't include the reading.
- Back: Structure using HTML for readability:
  • <strong>Reading:</strong> <span style="font-size: 18px; background-color: #fff0f0; padding: 2px 6px; border-radius: 3px;">[hiragana reading]</span>
  • <strong>Meaning:</strong> English translation(s)
  • <em>Type:</em> [noun, verb, adjective, etc.]
  • <strong>Examples:</strong>
    <ul>
      <li>Japanese sentence → <em>English translation</em></li>
      <li>Japanese sentence → <em>English translation</em></li>
    </ul>
  • <strong>Collocations:</strong> Common phrases using the word
  • <div class="highlight">Usage notes or cultural context</div>
  • <em>Similar words:</em> How they differ (when relevant)

Focus only on authentic Japanese vocabulary: kanji compounds, native Japanese words in hiragana, and traditional Japanese expressions. Skip any katakana words (foreign loanwords like コーヒー, コンピューター), proper names, or English words that might appear in the text.

Use <strong> for key terms, <em> for emphasis, <ul><li> for lists, and background colors for highlighting.""",
            "Spanish Vocabulary": """Create Spanish vocabulary cards with HTML formatting:
- Front: <strong>Spanish word/phrase</strong>
- Back: Structure with HTML:
  • <strong>English meaning:</strong> translation
  • <em>Pronunciation:</em> <span style="font-style: italic; background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">[phonetic guide]</span>
  • <strong>Examples:</strong>
    <ul><li>Spanish sentence → <em>English translation</em></li></ul>
  • <strong>Gender/Type:</strong> [masculine/feminine, verb conjugation, etc.]
  • <div class="highlight">Usage notes or cultural context</div>""",
            "Historical Facts & Dates": """Create historical flashcards with structured HTML formatting:
- Front: <strong>Historical question or event prompt</strong>
- Back: Comprehensive answer using:
  • <strong>Date/Period:</strong> <span style="background-color: #fff0f0; padding: 2px 6px; border-radius: 3px;">specific timeframe</span>
  • <strong>Key Figures:</strong> Important people involved
  • <strong>What happened:</strong> Brief description of the event
  • <strong>Significance:</strong> Why it was important
  • <strong>Context:</strong> 
    <ul><li>Causes leading to the event</li><li>Consequences</li></ul>
  • <em>Connections:</em> Related events or impacts
Use <strong> for dates and names, <ul><li> for multiple points, and <div class="highlight"> for key significance.""",
            "Mathematical Formulas": """Create mathematical concept cards with clear HTML structure:
- Front: <strong>Mathematical concept or problem</strong>
- Back: Well-formatted explanation:
  • <strong>Formula:</strong> <code>mathematical expression</code>
  • <strong>Where:</strong>
    <ul>
      <li><code>variable</code> = definition</li>
      <li><code>variable</code> = definition</li>
    </ul>
  • <strong>When to use:</strong> Applications and conditions
  • <strong>Example:</strong>
    <ol><li>Step 1: <code>calculation</code></li><li>Step 2: <code>calculation</code></li></ol>
  • <em>Notes:</em> Important considerations or common mistakes
Use <code> for all mathematical expressions, <ol><li> for steps, and <strong> for key concepts.""",
            "Scientific Terms": """Create scientific terminology cards with structured HTML:
- Front: <strong>Scientific term or concept</strong>
- Back: Comprehensive definition with structure:
  • <strong>Definition:</strong> Clear, concise explanation
  • <em>Category:</em> Field of science (biology, chemistry, physics, etc.)
  • <strong>Key characteristics:</strong>
    <ul><li>Important feature 1</li><li>Important feature 2</li></ul>
  • <strong>Examples:</strong> Real-world applications or instances
  • <strong>Related terms:</strong> Connected concepts
  • <div class="highlight">Clinical/practical significance</div>
Use <strong> for definitions, <em> for scientific names, and <ul><li> for lists of characteristics.""",
            "Business & Finance": """Create business and finance cards with professional HTML formatting:
- Front: <strong>Business term or financial concept</strong>
- Back: Professional explanation with structure:
  • <strong>Definition:</strong> Clear business explanation
  • <strong>Purpose:</strong> Why it's used in business
  • <strong>Key components:</strong>
    <ul><li>Important element 1</li><li>Important element 2</li></ul>
  • <strong>Example:</strong> Real-world business scenario
  • <strong>Formula/Calculation:</strong> <code>relevant formula</code> (if applicable)
  • <em>Best practices:</em> When and how to apply
  • <span style="background-color: #ffe6e6; padding: 2px 4px; border-radius: 3px;">Risk factors:</span> Important considerations
Use <strong> for key terms, <code> for formulas, and background colors for risks vs benefits.""",
        }

    def process_file(
        self, file_input: Union[Image.Image, str], progress=gr.Progress()
    ) -> Tuple[str, str, str, str]:
        """Process uploaded file (image or PDF) to extract text.

        Args:
            file_input: Uploaded PIL Image or file path
            progress: Gradio progress tracker

        Returns:
            Tuple of (status_message, extracted_text, text_preview, sources_summary)
        """
        if file_input is None:
            return "❌ Please upload a file.", "", "", self.get_sources_summary()

        progress(0.1, desc="Processing file...")

        try:
            # Determine file type and set progress message
            if isinstance(file_input, str):
                file_type = "PDF" if file_input.lower().endswith(".pdf") else "file"
                filename = os.path.basename(file_input) if file_input else "uploaded_file"
                progress(0.3, desc=f"Extracting text from {file_type}...")
            else:
                file_type = "image"
                filename = f"image_{len(self.source_files) + 1}"
                progress(0.3, desc="Extracting text from image...")

            # Extract text using Gemini
            extracted_text = self.gemini_client.extract_text_from_file(file_input)

            progress(0.8, desc="Processing results...")

            if not extracted_text.strip():
                return (
                    f"⚠️ No text could be extracted from {filename}. Please try a different file.",
                    "",
                    "",
                    self.get_sources_summary(),
                )

            # Add to source files tracking
            source_info = {
                "filename": filename,
                "type": file_type,
                "text_length": len(extracted_text),
                "text": extracted_text,
                "timestamp": len(self.source_files) + 1,  # Simple counter
            }

            self.source_files.append(source_info)
            self.all_extracted_texts.append(extracted_text)

            # Update combined current text
            self.current_text = "\n\n".join(self.all_extracted_texts)

            # Create preview (first 500 characters of this file's text)
            preview = extracted_text[:500] + ("..." if len(extracted_text) > 500 else "")

            progress(1.0, desc="Complete!")

            total_chars = sum(len(text) for text in self.all_extracted_texts)
            sources_summary = self.get_sources_summary()

            return (
                f"✅ Successfully extracted {len(extracted_text)} characters from {filename}! Total: {total_chars} characters from {len(self.source_files)} source(s).",
                extracted_text,
                preview,
                sources_summary,
            )

        except Exception as e:
            return f"❌ Error processing file: {str(e)}", "", "", self.get_sources_summary()

    def generate_cards(
        self, learning_objective: str, num_cards: int, progress=gr.Progress()
    ) -> Tuple[str, str, str]:
        """Generate study cards based on all extracted texts and learning objective.

        Args:
            learning_objective: What the user wants to learn
            num_cards: Number of cards to generate
            progress: Gradio progress tracker

        Returns:
            Tuple of (status_message, cards_preview, download_info)
        """
        if not self.current_text.strip():
            return "❌ Please extract text from at least one file first.", "", ""

        if not learning_objective.strip():
            return "❌ Please describe what you want to learn.", "", ""

        if self.gemini_client is None:
            return (
                "❌ Gemini client not initialized. Please check your API key configuration.",
                "",
                "",
            )

        try:
            progress(0.2, desc="Generating study cards from all sources...")

            # Generate cards using Gemini with combined text from all sources
            new_cards = self.gemini_client.generate_study_cards(
                self.current_text, learning_objective, num_cards
            )

            progress(0.6, desc="Validating cards...")

            # Validate cards
            validation = self.card_generator.validate_cards(new_cards)

            if not validation["valid"]:
                error_msg = "❌ Generated cards have issues:\n" + "\n".join(validation["errors"])
                return error_msg, "", ""

            # Replace current cards with new ones (full regeneration)
            self.current_cards = new_cards
            self.current_card_index = 0  # Reset to first card

            # Select all cards by default
            self.selected_cards = list(range(len(self.current_cards)))

            progress(0.9, desc="Creating preview...")

            # Generate preview
            preview = self.card_generator.preview_cards(new_cards)

            progress(1.0, desc="Complete!")

            source_count = len(self.source_files)
            total_chars = sum(len(text) for text in self.all_extracted_texts)

            return (
                f"✅ Generated {len(new_cards)} study cards from {source_count} source(s) ({total_chars:,} characters)!",
                preview,
                f"Ready to download deck with {len(new_cards)} cards",
            )

        except Exception as e:
            return f"❌ Error generating cards: {str(e)}", "", ""

    def create_anki_deck(self, deck_name: str, progress=gr.Progress()) -> Tuple[str, Optional[str]]:
        """Create and download Anki deck file.

        Args:
            deck_name: Name for the Anki deck
            progress: Gradio progress tracker

        Returns:
            Tuple of (status_message, file_path_or_none)
        """
        if not self.current_cards:
            return "❌ No cards available. Please generate cards first.", None

        # Get selected cards or all cards if none selected
        cards_to_include = self.get_selected_cards()
        if not cards_to_include:
            # If no cards are selected, use all cards
            cards_to_include = self.current_cards
            selection_note = " (all cards - none were specifically selected)"
        else:
            selection_note = f" ({len(cards_to_include)} selected cards)"

        if not deck_name.strip():
            deck_name = "AI Study Cards"

        try:
            progress(0.3, desc="Creating Anki deck...")

            # Create the deck file with selected cards
            file_path = self.card_generator.create_deck(
                cards_to_include, deck_name, "Generated from image using Gemini AI"
            )

            progress(1.0, desc="Deck created!")

            return (
                f"✅ Anki deck '{deck_name}' created successfully with {len(cards_to_include)} cards{selection_note}! Click download to save the .apkg file.",
                file_path,
            )

        except Exception as e:
            return f"❌ Error creating Anki deck: {str(e)}", None

    def get_card_list(self) -> List[str]:
        """Get a list of card titles for the dropdown.

        Returns:
            List of card titles with indices
        """
        if not self.current_cards:
            return ["No cards generated"]

        card_list = []
        for i, card in enumerate(self.current_cards):
            front_preview = card.get("front", "No question")[:50]
            if len(front_preview) >= 50:
                front_preview += "..."
            card_list.append(f"Card {i+1}: {front_preview}")

        return card_list

    def render_current_card(self, show_answer: bool = False) -> Tuple[str, str, str, int, int]:
        """Render the current card in HTML format.

        Args:
            show_answer: Whether to show the answer side

        Returns:
            Tuple of (card_html, navigation_info, flip_button_text, current_index, total_cards)
        """
        if not self.current_cards:
            return (
                "<div style='text-align: center; padding: 20px;'>No cards available</div>",
                "No cards",
                "Show Answer",
                0,
                0,
            )

        card = self.current_cards[self.current_card_index]
        front = card.get("front", "No question")
        back = card.get("back", "No answer")

        # Create HTML for the card
        if show_answer:
            card_html = f"""
            <div class="card-preview" style="max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif;">
                <div style="background: #f8f9fa; border-left: 4px solid #007bff; padding: 20px; margin-bottom: 20px; border-radius: 8px;">
                    <h3 style="margin-top: 0; color: #000000 !important;">Question:</h3>
                    <div style="font-size: 16px; line-height: 1.5; color: #000000 !important;">{front}</div>
                </div>
                <div style="background: #e8f5e8; border-left: 4px solid #28a745; padding: 20px; border-radius: 8px;">
                    <h3 style="margin-top: 0; color: #000000 !important;">Answer:</h3>
                    <div style="font-size: 16px; line-height: 1.5; color: #000000 !important;">{back}</div>
                </div>
            </div>
            """
            flip_text = "Show Question Only"
        else:
            card_html = f"""
            <div class="card-preview" style="max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif;">
                <div style="background: #f8f9fa; border-left: 4px solid #007bff; padding: 20px; border-radius: 8px; text-align: center;">
                    <h3 style="margin-top: 0; color: #000000 !important;">Question:</h3>
                    <div style="font-size: 18px; line-height: 1.6; font-weight: 500; color: #000000 !important;">{front}</div>
                    <hr style="margin: 20px 0; border: none; border-top: 2px solid #dee2e6;">
                    <p style="color: #000000 !important; font-style: italic;">Click "Show Answer" to reveal the answer</p>
                </div>
            </div>
            """
            flip_text = "Show Answer"

        nav_info = f"Card {self.current_card_index + 1} of {len(self.current_cards)}"

        return (card_html, nav_info, flip_text, self.current_card_index, len(self.current_cards))

    def navigate_card(self, direction: str) -> Tuple[str, str, str]:
        """Navigate to next or previous card.

        Args:
            direction: 'next' or 'prev'

        Returns:
            Tuple of (card_html, navigation_info, flip_button_text)
        """
        if not self.current_cards:
            return self.render_current_card()[:3]

        if direction == "next" and self.current_card_index < len(self.current_cards) - 1:
            self.current_card_index += 1
        elif direction == "prev" and self.current_card_index > 0:
            self.current_card_index -= 1

        return self.render_current_card()[:3]

    def jump_to_card(self, card_selection: str) -> Tuple[str, str, str]:
        """Jump to a specific card based on dropdown selection.

        Args:
            card_selection: Selected card from dropdown

        Returns:
            Tuple of (card_html, navigation_info, flip_button_text)
        """
        if not self.current_cards or card_selection == "No cards generated":
            return self.render_current_card()[:3]

        try:
            # Extract card index from selection (format: "Card X: ...")
            card_num = int(card_selection.split(":")[0].replace("Card ", ""))
            self.current_card_index = card_num - 1
        except (ValueError, IndexError):
            pass  # Keep current index if parsing fails

        return self.render_current_card()[:3]

    def flip_card(self, current_flip_text: str) -> Tuple[str, str, str]:
        """Flip the current card to show/hide answer.

        Args:
            current_flip_text: Current state of the flip button

        Returns:
            Tuple of (card_html, navigation_info, flip_button_text)
        """
        show_answer = current_flip_text == "Show Answer"
        return self.render_current_card(show_answer)[:3]

    def get_prompt_choices(self) -> List[str]:
        """Get list of available prompt choices for the dropdown.

        Returns:
            List of prompt names
        """
        return list(self.prepared_prompts.keys())

    def get_prompt_description(self, prompt_name: str) -> str:
        """Get the description for a selected prompt.

        Args:
            prompt_name: Name of the selected prompt

        Returns:
            Prompt description or empty string for custom
        """
        return self.prepared_prompts.get(prompt_name, "")

    def get_card_selection_data(self) -> List[Dict[str, Union[str, bool]]]:
        """Get card data with selection status for the checkboxes.

        Returns:
            List of dictionaries with card info and selection status
        """
        if not self.current_cards:
            return []

        card_data = []
        for i, card in enumerate(self.current_cards):
            front_preview = card.get("front", "No question")[:80]
            if len(front_preview) >= 80:
                front_preview += "..."

            # Remove HTML tags for preview
            front_clean = re.sub(r"<[^>]+>", "", front_preview)

            card_data.append(
                {
                    "index": i,
                    "preview": f"Card {i+1}: {front_clean}",
                    "selected": i in self.selected_cards,
                    "front": card.get("front", ""),
                    "back": card.get("back", ""),
                }
            )

        return card_data

    def update_card_selection(self, selected_indices: List[int]) -> str:
        """Update which cards are selected for deck creation.

        Args:
            selected_indices: List of card indices that are selected

        Returns:
            Status message about selection
        """
        if not self.current_cards:
            return "No cards available to select"

        self.selected_cards = selected_indices
        selected_count = len(selected_indices)
        total_count = len(self.current_cards)

        return f"Selected {selected_count} of {total_count} cards for deck creation"

    def get_selected_cards(self) -> List[Dict[str, str]]:
        """Get only the selected cards for deck creation.

        Returns:
            List of selected card dictionaries
        """
        if not self.current_cards or not self.selected_cards:
            return []

        return [self.current_cards[i] for i in self.selected_cards if i < len(self.current_cards)]

    def get_sources_summary(self) -> str:
        """Get a summary of all processed source files.

        Returns:
            Formatted string summarizing all source files
        """
        if not self.source_files:
            return "No files processed yet"

        summary_lines = ["📁 **Processed Sources:**"]
        total_chars = 0

        for i, source in enumerate(self.source_files, 1):
            total_chars += source["text_length"]
            summary_lines.append(
                f"  {i}. **{source['filename']}** ({source['type']}) - {source['text_length']:,} characters"
            )

        summary_lines.append(
            f"\n**Total:** {len(self.source_files)} files, {total_chars:,} characters"
        )
        return "\n".join(summary_lines)

    def clear_all_sources(self) -> Tuple[str, str, str]:
        """Clear all processed sources and start fresh.

        Returns:
            Tuple of (status_message, empty_text, sources_summary)
        """
        self.source_files = []
        self.all_extracted_texts = []
        self.current_text = ""
        self.current_cards = []
        self.cards_by_source = {}
        self.selected_cards = []
        self.current_card_index = 0

        return (
            "🗑️ All sources and cards cleared. Ready for new files.",
            "",
            self.get_sources_summary(),
        )

    def generate_cards_from_latest_source(
        self, learning_objective: str, num_cards: int, progress=gr.Progress()
    ) -> Tuple[str, str, str]:
        """Generate cards from the most recently added source only.

        Args:
            learning_objective: What the user wants to learn
            num_cards: Number of cards to generate
            progress: Gradio progress tracker

        Returns:
            Tuple of (status_message, cards_preview, download_info)
        """
        if not self.source_files:
            return "❌ Please add at least one source file first.", "", ""

        if not learning_objective.strip():
            return "❌ Please describe what you want to learn.", "", ""

        if self.gemini_client is None:
            return (
                "❌ Gemini client not initialized. Please check your API key configuration.",
                "",
                "",
            )

        try:
            progress(0.2, desc="Generating cards from latest source...")

            # Use only the most recent source
            latest_source = self.source_files[-1]
            latest_text = latest_source["text"]

            # Generate cards using Gemini for this source only
            new_cards = self.gemini_client.generate_study_cards(
                latest_text, learning_objective, num_cards
            )

            progress(0.6, desc="Validating cards...")

            # Validate cards
            validation = self.card_generator.validate_cards(new_cards)

            if not validation["valid"]:
                error_msg = "❌ Generated cards have issues:\n" + "\n".join(validation["errors"])
                return error_msg, "", ""

            # Track which cards came from which source
            source_index = len(self.source_files) - 1
            self.cards_by_source[source_index] = new_cards

            # Add new cards to the existing collection
            self.current_cards.extend(new_cards)

            # Update selected cards to include all cards by default
            self.selected_cards = list(range(len(self.current_cards)))

            progress(0.9, desc="Creating preview...")

            # Generate preview for all cards
            preview = self.card_generator.preview_cards(self.current_cards)

            progress(1.0, desc="Complete!")

            return (
                f"✅ Generated {len(new_cards)} new cards from '{latest_source['filename']}'! Total cards: {len(self.current_cards)}",
                preview,
                f"Ready to download deck with {len(self.current_cards)} cards",
            )

        except Exception as e:
            return f"❌ Error generating cards: {str(e)}", "", ""

    # ...existing code...


def create_interface():
    """Create and return the Gradio interface."""
    app = AnkiCardCreatorApp()

    # Custom CSS for better styling
    css = """
    .gradio-container {
        max-width: 1200px !important;
    }
    .status-box {
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .success {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .error {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
    }
    .info {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
    }
    /* Force black text in card preview areas */
    .card-preview * {
        color: #000000 !important;
    }
    .card-preview h1, .card-preview h2, .card-preview h3, .card-preview h4, .card-preview h5, .card-preview h6 {
        color: #000000 !important;
    }
    .card-preview p, .card-preview div, .card-preview span {
        color: #000000 !important;
    }
    """

    with gr.Blocks(title="AI Anki Card Creator", css=css, theme=gr.themes.Soft()) as interface:
        gr.Markdown(
            """
        # 🎯 AI Anki Card Creator
        
        Upload multiple images or PDFs with text, describe what you want to learn, and let AI create personalized Anki flashcards for you!
        
        **How it works:**
        1. 📷📄 Add one or more sources (images/PDFs) - each new file adds to your collection
        2. 📝 Describe your learning goals using prepared prompts or custom objectives
        3. 🤖 Generate cards from all sources OR add cards from just the latest source
        4. ✅ Select which cards to include in your deck
        5. 📚 Download your Anki deck (.apkg file)
        
        **Multi-source workflow:**
        - Add sources one by one to build your content collection
        - Generate from all sources to create a comprehensive deck
        - Add from latest source to incrementally expand existing cards
        - Use "Clear All" to start fresh
        """
        )

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 📷📄 Add Sources")
                gr.Markdown(
                    "💡 *You can add multiple files! Each new file will be added to your collection.*"
                )

                with gr.Tabs():
                    with gr.TabItem("📁 Upload File"):
                        file_input = gr.File(
                            label="Upload image or PDF file",
                            file_types=["image", ".pdf"],
                            type="filepath",
                        )

                    with gr.TabItem("📷 Take Photo"):
                        camera_input = gr.Image(
                            label="Take a photo", sources=["webcam"], type="pil", height=300
                        )

                    with gr.TabItem("🖼️ Upload Image"):
                        image_input = gr.Image(label="Upload an image", type="pil", height=300)

                with gr.Row():
                    process_btn = gr.Button("➕ Add Source", variant="primary", size="lg")
                    clear_sources_btn = gr.Button("🗑️ Clear All", variant="secondary", size="sm")

            with gr.Column(scale=1):
                gr.Markdown("### 📝 Extracted Text & Sources")
                extraction_status = gr.Textbox(label="Status", interactive=False, max_lines=2)

                sources_summary = gr.Markdown(
                    value="No files processed yet", label="Sources Summary"
                )

                text_preview = gr.Textbox(
                    label="Latest Text Preview",
                    interactive=False,
                    max_lines=6,
                    placeholder="Text from the most recent file will appear here...",
                )

        gr.Markdown("---")

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 🎯 Learning Objectives")

                prompt_selector = gr.Dropdown(
                    label="Choose a prepared prompt or create custom",
                    choices=app.get_prompt_choices(),
                    value="Custom (Enter your own)",
                    interactive=True,
                )

                learning_objective = gr.Textbox(
                    label="What do you want to learn?",
                    placeholder="e.g., vocabulary words, historical dates, math formulas, key concepts...",
                    max_lines=5,
                )

                num_cards = gr.Slider(
                    label="Number of cards to generate", minimum=1, maximum=50, value=10, step=1
                )

                gr.Markdown("### 🎲 Generation Options")
                gr.Markdown(
                    "**Generate from all sources:** Creates cards using text from all added files"
                )
                gr.Markdown(
                    "**Add from latest:** Generates additional cards from the most recently added file only"
                )

                with gr.Row():
                    generate_btn = gr.Button(
                        "🎲 Generate from All Sources", variant="primary", size="lg"
                    )
                    add_from_latest_btn = gr.Button(
                        "➕ Add from Latest Source", variant="secondary", size="lg"
                    )

            with gr.Column(scale=1):
                gr.Markdown("### 📋 Generated Cards Preview")
                generation_status = gr.Textbox(label="Status", interactive=False, max_lines=2)

                cards_preview = gr.Textbox(
                    label="Cards Preview",
                    interactive=False,
                    max_lines=10,
                    placeholder="Generated cards will appear here...",
                )

        gr.Markdown("---")

        # Card Preview Section
        with gr.Row():
            gr.Markdown("## 🎴 Card Viewer")

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 🗃️ Card Navigation")

                card_selector = gr.Dropdown(
                    label="Select Card",
                    choices=["No cards generated"],
                    value="No cards generated",
                    interactive=True,
                )

                with gr.Row():
                    prev_btn = gr.Button("◀️ Previous", size="sm")
                    flip_btn = gr.Button("🔄 Show Answer", size="sm", variant="secondary")
                    next_btn = gr.Button("Next ▶️", size="sm")

                card_nav_info = gr.Textbox(
                    label="Navigation Info", value="No cards", interactive=False, max_lines=1
                )

            with gr.Column(scale=2):
                gr.Markdown("### 👁️ Card Preview")

                card_display = gr.HTML(
                    value="<div style='text-align: center; padding: 40px; color: #666;'>Generate cards to see them here</div>",
                    label="Card Display",
                )

        gr.Markdown("---")

        # Card Selection Section
        with gr.Row():
            gr.Markdown("## ✅ Card Selection")

        with gr.Row():
            with gr.Column():
                gr.Markdown("### 📋 Select Cards for Deck")
                gr.Markdown(
                    "Choose which cards to include in your Anki deck. If no cards are selected, all cards will be included."
                )

                card_selection = gr.CheckboxGroup(
                    label="Cards to Include", choices=[], value=[], interactive=True
                )

                with gr.Row():
                    select_all_btn = gr.Button("✅ Select All", size="sm", variant="secondary")
                    deselect_all_btn = gr.Button("❌ Deselect All", size="sm", variant="secondary")

                selection_status = gr.Textbox(
                    label="Selection Status",
                    value="No cards generated yet",
                    interactive=False,
                    max_lines=1,
                )

        gr.Markdown("---")

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 📚 Create Anki Deck")
                deck_name = gr.Textbox(
                    label="Deck Name", placeholder="My Study Deck", value="AI Study Cards"
                )

                create_deck_btn = gr.Button("📦 Create Anki Deck", variant="primary", size="lg")

            with gr.Column(scale=1):
                deck_status = gr.Textbox(label="Status", interactive=False, max_lines=2)

                download_file = gr.File(label="Download Anki Deck (.apkg)", interactive=False)

        # Hidden components to store extracted text
        extracted_text_storage = gr.Textbox(visible=False)

        # Event handlers - handle file upload, camera, and direct image upload
        def process_file_or_image(file_path, camera_image, uploaded_image):
            """Process either file upload, camera capture, or direct image upload."""
            if file_path is not None:
                return app.process_file(file_path)
            elif camera_image is not None:
                return app.process_file(camera_image)
            elif uploaded_image is not None:
                return app.process_file(uploaded_image)
            else:
                return (
                    "❌ Please upload a file, take a photo, or upload an image.",
                    "",
                    "",
                    app.get_sources_summary(),
                )

        def clear_all_sources():
            """Clear all sources and reset the application."""
            status, text, sources = app.clear_all_sources()
            return (
                status,
                text,
                sources,
                gr.Dropdown(choices=["No cards generated"], value="No cards generated"),
                "<div style='text-align: center; padding: 40px; color: #666;'>Add sources and generate cards to see them here</div>",
                "No cards",
                "Show Answer",
                gr.CheckboxGroup(choices=[], value=[]),
                "No cards generated yet",
            )

        def update_prompt_description(prompt_name):
            """Update the learning objective textbox when a prepared prompt is selected."""
            description = app.get_prompt_description(prompt_name)
            if prompt_name == "Custom (Enter your own)":
                return ""
            else:
                return description

        def generate_cards_and_update_viewer(learning_objective, num_cards):
            """Generate cards from all sources and update the card viewer."""
            status, preview, download_info = app.generate_cards(learning_objective, num_cards)
            return _update_viewer_after_generation((status, preview, download_info))

        def add_cards_from_latest_and_update_viewer(learning_objective, num_cards):
            """Add cards from latest source and update the card viewer."""
            status, preview, download_info = app.generate_cards_from_latest_source(
                learning_objective, num_cards
            )
            return _update_viewer_after_generation((status, preview, download_info))

        def _update_viewer_after_generation(result):
            """Helper function to update the viewer after card generation."""
            status, preview, download_info = result

            # Update card selector dropdown
            card_choices = app.get_card_list()

            # Update card selection checkboxes
            if app.current_cards:
                # Create card selection choices
                selection_choices = []
                for i, card in enumerate(app.current_cards):
                    front_preview = card.get("front", "No question")[:60]
                    if len(front_preview) >= 60:
                        front_preview += "..."
                    # Remove HTML tags for preview
                    front_clean = re.sub(r"<[^>]+>", "", front_preview)
                    selection_choices.append(f"Card {i+1}: {front_clean}")

                card_html, nav_info, flip_text, _, _ = app.render_current_card()
                selection_status = f"Selected {len(app.selected_cards)} of {len(app.current_cards)} cards for deck creation"

                return (
                    status,  # generation_status
                    preview,  # cards_preview
                    download_info,  # deck_status
                    gr.Dropdown(
                        choices=card_choices, value=card_choices[0], interactive=True
                    ),  # card_selector
                    card_html,  # card_display
                    nav_info,  # card_nav_info
                    flip_text,  # flip_btn
                    gr.CheckboxGroup(
                        choices=selection_choices, value=selection_choices, interactive=True
                    ),  # card_selection
                    selection_status,  # selection_status
                )
            else:
                return (
                    status,  # generation_status
                    preview,  # cards_preview
                    download_info,  # deck_status
                    gr.Dropdown(
                        choices=["No cards generated"], value="No cards generated", interactive=True
                    ),  # card_selector
                    "<div style='text-align: center; padding: 40px; color: #666;'>Generate cards to see them here</div>",  # card_display
                    "No cards",  # card_nav_info
                    "Show Answer",  # flip_btn
                    gr.CheckboxGroup(choices=[], value=[], interactive=True),  # card_selection
                    "No cards generated yet",  # selection_status
                )

        # File processing event handlers
        process_btn.click(  # pylint: disable=no-member
            fn=process_file_or_image,
            inputs=[file_input, camera_input, image_input],
            outputs=[extraction_status, extracted_text_storage, text_preview, sources_summary],
        )

        clear_sources_btn.click(  # pylint: disable=no-member
            fn=clear_all_sources,
            outputs=[
                extraction_status,
                text_preview,
                sources_summary,
                card_selector,
                card_display,
                card_nav_info,
                flip_btn,
                card_selection,
                selection_status,
            ],
        )

        # Update prompt description when a prepared prompt is selected
        prompt_selector.change(  # pylint: disable=no-member
            fn=update_prompt_description, inputs=[prompt_selector], outputs=[learning_objective]
        )

        # Card generation event handlers
        generate_btn.click(  # pylint: disable=no-member
            fn=generate_cards_and_update_viewer,
            inputs=[learning_objective, num_cards],
            outputs=[
                generation_status,
                cards_preview,
                deck_status,
                card_selector,
                card_display,
                card_nav_info,
                flip_btn,
                card_selection,
                selection_status,
            ],
        )

        add_from_latest_btn.click(  # pylint: disable=no-member
            fn=add_cards_from_latest_and_update_viewer,
            inputs=[learning_objective, num_cards],
            outputs=[
                generation_status,
                cards_preview,
                deck_status,
                card_selector,
                card_display,
                card_nav_info,
                flip_btn,
                card_selection,
                selection_status,
            ],
        )

        # Card selection event handlers
        def update_selection(selected_choices):
            """Update card selection based on checkbox choices."""
            if not app.current_cards:
                return "No cards available to select"

            # Extract indices from selected choices
            selected_indices = []
            for choice in selected_choices:
                try:
                    # Extract card number from "Card X: ..." format
                    card_num = int(choice.split(":")[0].replace("Card ", ""))
                    selected_indices.append(card_num - 1)  # Convert to 0-based index
                except (ValueError, IndexError):
                    continue

            return app.update_card_selection(selected_indices)

        def select_all_cards():
            """Select all available cards."""
            if not app.current_cards:
                return gr.CheckboxGroup(choices=[], value=[]), "No cards available"

            # Get all card choices
            selection_choices = []
            for i, card in enumerate(app.current_cards):
                front_preview = card.get("front", "No question")[:60]
                if len(front_preview) >= 60:
                    front_preview += "..."
                # Remove HTML tags for preview
                front_clean = re.sub(r"<[^>]+>", "", front_preview)
                selection_choices.append(f"Card {i+1}: {front_clean}")

            # Select all cards
            app.selected_cards = list(range(len(app.current_cards)))
            status = app.update_card_selection(app.selected_cards)

            return gr.CheckboxGroup(choices=selection_choices, value=selection_choices), status

        def deselect_all_cards():
            """Deselect all cards."""
            if not app.current_cards:
                return gr.CheckboxGroup(choices=[], value=[]), "No cards available"

            # Get all card choices but select none
            selection_choices = []
            for i, card in enumerate(app.current_cards):
                front_preview = card.get("front", "No question")[:60]
                if len(front_preview) >= 60:
                    front_preview += "..."
                # Remove HTML tags for preview
                front_clean = re.sub(r"<[^>]+>", "", front_preview)
                selection_choices.append(f"Card {i+1}: {front_clean}")

            # Deselect all cards
            app.selected_cards = []
            status = app.update_card_selection(app.selected_cards)

            return gr.CheckboxGroup(choices=selection_choices, value=[]), status

        card_selection.change(  # pylint: disable=no-member
            fn=update_selection, inputs=[card_selection], outputs=[selection_status]
        )

        select_all_btn.click(fn=select_all_cards, outputs=[card_selection, selection_status])  # pylint: disable=no-member

        deselect_all_btn.click(fn=deselect_all_cards, outputs=[card_selection, selection_status])  # pylint: disable=no-member

        # Card navigation event handlers
        prev_btn.click(  # pylint: disable=no-member
            fn=lambda: app.navigate_card("prev"), outputs=[card_display, card_nav_info, flip_btn]
        )

        next_btn.click(  # pylint: disable=no-member
            fn=lambda: app.navigate_card("next"), outputs=[card_display, card_nav_info, flip_btn]
        )

        flip_btn.click(  # pylint: disable=no-member
            fn=app.flip_card, inputs=[flip_btn], outputs=[card_display, card_nav_info, flip_btn]
        )

        card_selector.change(  # pylint: disable=no-member
            fn=app.jump_to_card,
            inputs=[card_selector],
            outputs=[card_display, card_nav_info, flip_btn],
        )

        create_deck_btn.click(  # pylint: disable=no-member
            fn=app.create_anki_deck, inputs=[deck_name], outputs=[deck_status, download_file]
        )

    return interface


def main():
    """Main entry point for the application."""
    interface = create_interface()

    # Get port from environment variable (for Cloud Run) or default to 7860
    host = os.getenv("HOST", "0.0.0.0")
    port_str = os.getenv("PORT", "7860")
    port = int(port_str)

    # Get authentication credentials from environment variables
    valid_username = os.getenv("USERNAME")
    valid_password = os.getenv("PASSWORD")

    # Simple authentication function for Gradio
    def authenticate_user(username: str, password: str) -> bool:
        return username == valid_username and password == valid_password

    interface.launch(
        server_name=host,
        server_port=port,
        share=False,
        debug=os.getenv("ENVIRONMENT", "development") == "development",
        auth=authenticate_user,
    )


if __name__ == "__main__":
    main()
