import random
import tempfile
import os
import zipfile
import sqlite3
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import genanki


class AnkiCardGenerator:
    """Generate Anki-compatible flashcard decks from study card data."""

    def __init__(self):
        """Initialize the Anki card generator with a custom note type."""
        # Create a custom note type for our study cards
        self.note_type = genanki.Model(
            random.randrange(1 << 30, 1 << 31),  # Random model ID
            "AI Study Card",
            fields=[
                {"name": "Front"},
                {"name": "Back"},
                {"name": "Source"},
                {"name": "Created"},
            ],
            templates=[
                {
                    "name": "Card 1",
                    "qfmt": """
                    <div class="card-front">
                        <div class="question">{{Front}}</div>
                        <div class="source">Source: {{Source}}</div>
                    </div>
                    """,
                    "afmt": """
                    <div class="card-back">
                        <div class="question">{{Front}}</div>
                        <hr>
                        <div class="answer">{{Back}}</div>
                        <div class="metadata">
                            <div class="source">Source: {{Source}}</div>
                            <div class="created">Created: {{Created}}</div>
                        </div>
                    </div>
                    """,
                },
            ],
            css="""
            .card {
                font-family: "Arial", sans-serif;
                font-size: 16px;
                line-height: 1.5;
                color: #000000;
                background-color: #fafafa;
                padding: 20px;
                border-radius: 8px;
                max-width: 600px;
                margin: 0 auto;
            }
            
            .card-front, .card-back {
                text-align: center;
            }
            
            .question {
                font-size: 18px;
                font-weight: bold;
                margin-bottom: 20px;
                color: #000000;
                background-color: #ecf0f1;
                padding: 15px;
                border-radius: 5px;
                border-left: 4px solid #3498db;
            }
            
            .answer {
                font-size: 16px;
                margin: 20px 0;
                padding: 15px;
                background-color: #e8f5e8;
                border-radius: 5px;
                border-left: 4px solid #27ae60;
                text-align: left;
                color: #000000;
            }
            
            .source {
                font-size: 12px;
                color: #000000;
                font-style: italic;
                margin-top: 10px;
            }
            
            .metadata {
                margin-top: 20px;
                padding-top: 15px;
                border-top: 1px solid #bdc3c7;
                font-size: 11px;
                color: #000000;
            }
            
            .created {
                margin-top: 5px;
            }
            
            hr {
                border: none;
                border-top: 2px solid #ecf0f1;
                margin: 20px 0;
            }
            
            /* Enhanced formatting for structured content */
            strong, b {
                color: #000000;
                font-weight: bold;
            }
            
            em, i {
                color: #000000;
                font-style: italic;
            }
            
            .highlight {
                background-color: #fff3cd;
                border: 1px solid #ffeaa7;
                border-radius: 4px;
                padding: 8px;
                margin: 5px 0;
                color: #000000;
            }
            
            ul, ol {
                margin: 10px 0;
                padding-left: 20px;
                text-align: left;
                color: #000000;
            }
            
            li {
                margin: 5px 0;
                line-height: 1.4;
                color: #000000;
            }
            
            code {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 3px;
                padding: 2px 6px;
                font-family: "Monaco", "Consolas", monospace;
                font-size: 14px;
                color: #000000;
            }
            
            blockquote {
                border-left: 4px solid #6c757d;
                margin: 10px 0;
                padding: 10px 15px;
                background-color: #f8f9fa;
                font-style: italic;
                color: #000000;
            }
            
            /* Color classes for different types of information */
            .definition {
                color: #000000;
                font-weight: bold;
            }
            
            .example {
                color: #000000;
                font-style: italic;
            }
            
            .warning {
                color: #000000;
                font-weight: bold;
                background-color: #ffe6e6;
                padding: 2px 4px;
                border-radius: 3px;
            }
            
            .note {
                color: #000000;
                font-size: 14px;
            }
            
            .pronunciation {
                color: #000000;
                font-style: italic;
                font-size: 14px;
            }
            
            /* Responsive design */
            @media (max-width: 600px) {
                .card {
                    padding: 15px;
                    font-size: 14px;
                }
                
                .question {
                    font-size: 16px;
                }
                
                .answer {
                    font-size: 14px;
                }
                
                ul, ol {
                    padding-left: 15px;
                }
            }
            """,
        )

    def create_deck(
        self, cards: List[Dict[str, str]], deck_name: str, source_info: str = "AI Generated"
    ) -> str:
        """Create an Anki deck (.apkg file) from study cards.

        Args:
            cards: List of dictionaries with 'front' and 'back' keys
            deck_name: Name for the Anki deck
            source_info: Information about the source material

        Returns:
            Path to the created .apkg file
        """
        if not cards:
            raise ValueError("No cards provided to create deck")

        # Create the deck
        deck_id = random.randrange(1 << 30, 1 << 31)
        deck = genanki.Deck(deck_id, deck_name)

        # Get current timestamp
        created_time = datetime.now().strftime("%Y-%m-%d %H:%M")

        # Add cards to the deck
        for i, card_data in enumerate(cards, 1):
            front = card_data.get("front", f"Question {i}")
            back = card_data.get("back", f"Answer {i}")

            # Create note
            note = genanki.Note(
                model=self.note_type, fields=[front, back, source_info, created_time]
            )

            deck.add_note(note)

        # Create temporary file for the deck
        temp_dir = tempfile.gettempdir()
        filename = f"{deck_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.apkg"
        file_path = os.path.join(temp_dir, filename)

        # Generate the .apkg file
        package = genanki.Package(deck)
        package.write_to_file(file_path)

        return file_path

    def validate_cards(self, cards: List[Dict[str, str]]) -> Dict[str, Any]:
        """Validate card data and return statistics.

        Args:
            cards: List of card dictionaries

        Returns:
            Dictionary with validation results and statistics
        """
        if not cards:
            return {"valid": False, "error": "No cards provided", "total_cards": 0}

        valid_cards = 0
        invalid_cards = []

        for i, card in enumerate(cards):
            if not isinstance(card, dict):
                invalid_cards.append(f"Card {i+1}: Not a dictionary")
                continue

            if not card.get("front") or not str(card.get("front")).strip():
                invalid_cards.append(f"Card {i+1}: Missing or empty front")
                continue

            if not card.get("back") or not str(card.get("back")).strip():
                invalid_cards.append(f"Card {i+1}: Missing or empty back")
                continue

            valid_cards += 1

        return {
            "valid": len(invalid_cards) == 0,
            "total_cards": len(cards),
            "valid_cards": valid_cards,
            "invalid_cards": len(invalid_cards),
            "errors": invalid_cards,
        }

    def preview_cards(self, cards: List[Dict[str, str]], max_preview: int = 3) -> str:
        """Generate a text preview of the cards.

        Args:
            cards: List of card dictionaries
            max_preview: Maximum number of cards to preview

        Returns:
            Formatted string preview of the cards
        """
        if not cards:
            return "No cards to preview."

        preview_text = f"Preview of {min(len(cards), max_preview)} cards (Total: {len(cards)}):\n\n"

        for i, card in enumerate(cards[:max_preview]):
            front = card.get("front", "No question")
            back = card.get("back", "No answer")

            preview_text += f"--- Card {i+1} ---\n"
            preview_text += f"Q: {front[:100]}{'...' if len(front) > 100 else ''}\n"
            preview_text += f"A: {back[:100]}{'...' if len(back) > 100 else ''}\n\n"

        if len(cards) > max_preview:
            preview_text += f"... and {len(cards) - max_preview} more cards"

        return preview_text

    def read_deck(self, file_path: str) -> Tuple[str, List[Dict[str, str]]]:
        """Read an Anki deck (.apkg file) and extract cards.

        Args:
            file_path: Path to the .apkg file

        Returns:
            Tuple with deck name and list of cards (front and back)
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Deck file not found: {file_path}")

        # Extract the .apkg file (which is a zip file)
        with zipfile.ZipFile(file_path, "r") as zip_ref:
            zip_ref.extractall(tempfile.gettempdir())
            extracted_files = zip_ref.namelist()

        # Find the SQLite database file in the extracted files
        db_file = next((f for f in extracted_files if f.endswith(".db")), None)
        if not db_file:
            raise ValueError("No database file found in the deck package")

        # Connect to the SQLite database and read the cards
        conn = sqlite3.connect(os.path.join(tempfile.gettempdir(), db_file))
        cursor = conn.cursor()

        # Query the notes table to get the card data
        cursor.execute("SELECT flds FROM notes")
        rows = cursor.fetchall()

        # Close the database connection
        conn.close()

        # Extract the front and back fields from the card data
        cards = []
        for row in rows:
            fields = row[0].split("\x1f")  # Fields are separated by a special character
            if len(fields) >= 2:
                cards.append({"front": fields[0], "back": fields[1]})

        # Get the deck name (usually the first part of the .apkg file name)
        deck_name = os.path.basename(file_path).split(".")[0]

        return deck_name, cards

    def export_deck_to_json(self, file_path: str, output_path: Optional[str] = None) -> str:
        """Export an Anki deck (.apkg file) to a JSON file.

        Args:
            file_path: Path to the .apkg file
            output_path: Optional path for the output JSON file

        Returns:
            Path to the exported JSON file
        """
        deck_name, cards = self.read_deck(file_path)

        # Prepare the output JSON data
        output_data = {"deck_name": deck_name, "cards": cards}

        # Determine the output file path
        if output_path is None:
            output_path = os.path.splitext(file_path)[0] + ".json"

        # Write the data to the JSON file
        with open(output_path, "w", encoding="utf-8") as json_file:
            json.dump(output_data, json_file, ensure_ascii=False, indent=4)

        return output_path

    def import_cards_from_json(self, json_path: str) -> Tuple[str, List[Dict[str, str]]]:
        """Import cards from a JSON file and return as deck data.

        Args:
            json_path: Path to the JSON file

        Returns:
            Tuple with deck name and list of cards (front and back)
        """
        if not os.path.exists(json_path):
            raise FileNotFoundError(f"JSON file not found: {json_path}")

        # Read the JSON data from the file
        with open(json_path, "r", encoding="utf-8") as json_file:
            data = json.load(json_file)

        deck_name = data.get("deck_name", "Imported Deck")
        cards = data.get("cards", [])

        return deck_name, cards

    def parse_existing_deck(
        self, apkg_file_path: str
    ) -> Tuple[List[Dict[str, str]], Dict[str, Any]]:
        """Parse an existing Anki deck (.apkg file) and extract cards.

        Args:
            apkg_file_path: Path to the .apkg file

        Returns:
            Tuple of (cards_list, deck_metadata)
        """
        cards = []
        deck_metadata = {"name": "", "description": "", "model_info": {}}

        try:
            # Create temporary directory to extract the .apkg file
            with tempfile.TemporaryDirectory() as temp_dir:
                # Extract the .apkg (zip) file
                with zipfile.ZipFile(apkg_file_path, "r") as zip_file:
                    zip_file.extractall(temp_dir)

                # Look for the collection.anki2 database
                db_path = os.path.join(temp_dir, "collection.anki2")
                if not os.path.exists(db_path):
                    raise ValueError("Invalid Anki deck file: missing collection.anki2")

                # Connect to the SQLite database
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()

                # Get deck information
                cursor.execute("SELECT decks FROM col")
                deck_data = cursor.fetchone()
                if deck_data:
                    decks_json = json.loads(deck_data[0])
                    # Get the first deck (usually the only one in a single deck export)
                    for deck_id, deck_info in decks_json.items():
                        if deck_id != "1":  # Skip the default deck
                            deck_metadata["name"] = deck_info.get("name", "")
                            deck_metadata["description"] = deck_info.get("desc", "")
                            break

                # Get model information for field mapping
                cursor.execute("SELECT models FROM col")
                models_data = cursor.fetchone()
                if models_data:
                    models_json = json.loads(models_data[0])
                    deck_metadata["model_info"] = models_json

                # Get cards and notes
                cursor.execute(
                    """
                    SELECT n.flds, n.tags, c.type 
                    FROM notes n 
                    JOIN cards c ON c.nid = n.id 
                    WHERE c.did != 1
                """
                )

                note_rows = cursor.fetchall()

                for fields_str, tags, card_type in note_rows:
                    # Split fields by the field separator (ASCII 31)
                    fields = fields_str.split("\x1f")

                    # Map fields to front/back based on common patterns
                    if len(fields) >= 2:
                        front = fields[0].strip()
                        back = fields[1].strip()

                        # Clean HTML tags for preview (basic cleaning)
                        front = self._clean_html(front)
                        back = self._clean_html(back)

                        if front and back:  # Only add if both front and back exist
                            card = {
                                "front": front,
                                "back": back,
                                "tags": tags,
                                "card_type": card_type,
                            }
                            cards.append(card)

                conn.close()

        except Exception as e:
            raise Exception(f"Error parsing Anki deck: {str(e)}")

        return cards, deck_metadata

    def _clean_html(self, text: str) -> str:
        """Basic HTML tag removal for display purposes.

        Args:
            text: Text potentially containing HTML tags

        Returns:
            Cleaned text
        """
        import re

        # Remove HTML tags
        clean_text = re.sub(r"<[^>]+>", "", text)
        # Replace HTML entities
        clean_text = clean_text.replace("&nbsp;", " ")
        clean_text = clean_text.replace("&lt;", "<")
        clean_text = clean_text.replace("&gt;", ">")
        clean_text = clean_text.replace("&amp;", "&")
        return clean_text.strip()

    def extend_deck(
        self,
        existing_cards: List[Dict[str, str]],
        new_cards: List[Dict[str, str]],
        deck_name: str,
        source_info: str = "AI Generated",
    ) -> str:
        """Create an extended Anki deck by combining existing cards with new ones.

        Args:
            existing_cards: List of existing card dictionaries
            new_cards: List of new card dictionaries to add
            deck_name: Name for the extended Anki deck
            source_info: Information about the source material for new cards

        Returns:
            Path to the created .apkg file
        """
        if not new_cards and not existing_cards:
            raise ValueError("No cards provided to create deck")

        # Combine all cards
        all_cards = existing_cards + new_cards

        # Create the deck using the existing create_deck method
        return self.create_deck(all_cards, deck_name, source_info)
