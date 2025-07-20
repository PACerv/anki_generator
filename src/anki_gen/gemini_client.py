import os
from typing import Optional, List, Dict, Union
from PIL import Image
import google.generativeai as genai


class GeminiClient:
    """Client for interacting with Google's Gemini AI for OCR and content generation."""

    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-1.5-flash"):
        """Initialize the Gemini client.

        Args:
            api_key: Google API key. If None, will try to get from environment.
            model_name: Name of the Gemini model to use.
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("Google API key is required. Set GOOGLE_API_KEY environment variable.")

        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model_name)

    def extract_text_from_image(self, image: Image.Image) -> str:
        """Extract text content from an image using Gemini Vision.

        Args:
            image: PIL Image object

        Returns:
            Extracted text content
        """
        try:
            prompt = """
            Please extract ALL text content from this image. Include:
            - All visible text, headings, and labels
            - Any structured information (lists, tables, etc.)
            - Mathematical formulas or equations
            - Preserve the general structure and formatting where possible
            
            Return only the extracted text content without any additional commentary.
            """

            response = self.model.generate_content([prompt, image])
            return response.text.strip()

        except Exception as e:
            raise Exception(f"Error extracting text from image: {str(e)}")

    def extract_text_from_pdf(self, pdf_file_path: str) -> str:
        """Extract text content from a PDF file using Gemini.

        Args:
            pdf_file_path: Path to the PDF file

        Returns:
            Extracted text content
        """
        try:
            # Upload the PDF file to Gemini
            pdf_file = genai.upload_file(pdf_file_path)

            prompt = """
            Please extract ALL text content from this PDF document. Include:
            - All visible text, headings, and labels
            - Any structured information (lists, tables, etc.)
            - Mathematical formulas or equations
            - Preserve the general structure and formatting where possible
            - Include page breaks or section separators where appropriate
            
            Return only the extracted text content without any additional commentary.
            """

            response = self.model.generate_content([prompt, pdf_file])

            # Clean up the uploaded file
            genai.delete_file(pdf_file.name)

            return response.text.strip()

        except Exception as e:
            raise Exception(f"Error extracting text from PDF: {str(e)}")

    def extract_text_from_file(self, file_input: Union[Image.Image, str]) -> str:
        """Extract text from either an image or PDF file.

        Args:
            file_input: Either a PIL Image object or path to an image/PDF file

        Returns:
            Extracted text content
        """
        if isinstance(file_input, Image.Image):
            return self.extract_text_from_image(file_input)
        elif isinstance(file_input, str):
            if file_input.lower().endswith(".pdf"):
                return self.extract_text_from_pdf(file_input)
            elif file_input.lower().endswith(
                (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp")
            ):
                # Load image file and extract text
                image = Image.open(file_input)
                return self.extract_text_from_image(image)
            else:
                raise ValueError(
                    "Unsupported file type. Please provide an image file (PNG, JPG, etc.) or PDF file."
                )
        else:
            raise ValueError("Unsupported file type. Please provide a PIL Image or file path.")

    def generate_study_cards(
        self, extracted_text: str, learning_objective: str, num_cards: int = 10
    ) -> List[Dict[str, str]]:
        """Generate study cards based on extracted text and learning objectives.

        Args:
            extracted_text: Text extracted from the image
            learning_objective: What the user wants to learn (e.g., "vocabulary", "historical facts")
            num_cards: Number of cards to generate

        Returns:
            List of dictionaries with 'front' and 'back' keys for each card
        """
        try:
            prompt = f"""
            Based on the following extracted text and learning objective, create {num_cards} study cards suitable for spaced repetition learning (like Anki flashcards).

            EXTRACTED TEXT:
            {extracted_text}

            LEARNING OBJECTIVE:
            {learning_objective}

            INSTRUCTIONS:
            1. Create exactly {num_cards} flashcards
            2. Each card should have a clear, concise FRONT (question/prompt) and BACK (answer/explanation)
            3. Focus on the most important information related to the learning objective
            4. Make questions specific and testable
            5. Include context when necessary for clarity
            6. Vary question types (definitions, examples, applications, etc.)
            7. Use HTML formatting to make the cards more readable and well-structured

            HTML FORMATTING GUIDELINES:
            - Use <strong> or <b> for important terms, keywords, and emphasis
            - Use <em> or <i> for foreign words, scientific names, or subtle emphasis
            - Use <br> for line breaks when needed
            - Use <ul> and <li> for bullet points when listing multiple items
            - Use <ol> and <li> for numbered lists when showing steps or rankings
            - Use <div class="highlight"> for key concepts that need special attention
            - Use <span style="background-color: #ffe6e6; padding: 2px 4px; border-radius: 3px;"> for critical information or warnings
            - Use <span style="background-color: #e6f3e6; padding: 2px 4px; border-radius: 3px;"> for positive examples or correct answers
            - Use <code> for formulas, equations, or technical terms
            - Use <blockquote> for quotes or important excerpts
            - For definitions: Use <strong> for the term being defined
            - For examples: Use <em>Example:</em> to introduce examples
            - For pronunciation: Use <span style="font-style: italic;">pronunciation guide</span>
            - Always ensure text remains BLACK (#000000) for maximum readability

            CONTENT STRUCTURE EXAMPLES:
            - For vocabulary: <strong>Word</strong><br><em>pronunciation</em><br>Definition with <strong>key points</strong>
            - For concepts: <strong>Main Concept</strong><br><ul><li>Key point 1</li><li>Key point 2</li></ul>
            - For formulas: <code>Formula</code><br><strong>Where:</strong><br><ul><li>Variable 1 = explanation</li></ul>
            - For historical facts: <strong>Event/Date</strong><br><em>Context:</em> background<br><strong>Significance:</strong> importance

            FORMAT YOUR RESPONSE AS:
            CARD 1:
            FRONT: [Question or prompt with HTML formatting]
            BACK: [Answer or explanation with HTML formatting for better structure]

            CARD 2:
            FRONT: [Question or prompt with HTML formatting]
            BACK: [Answer or explanation with HTML formatting for better structure]

            ...and so on for all {num_cards} cards.
            """

            response = self.model.generate_content(prompt)
            return self._parse_cards_response(response.text)

        except Exception as e:
            raise Exception(f"Error generating study cards: {str(e)}")

    def _parse_cards_response(self, response_text: str) -> List[Dict[str, str]]:
        """Parse the AI response into structured card data.

        Args:
            response_text: Raw response from Gemini

        Returns:
            List of card dictionaries
        """
        cards = []
        lines = response_text.strip().split("\n")
        current_card = {}

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith("CARD "):
                # Save previous card if exists
                if current_card.get("front") and current_card.get("back"):
                    cards.append(current_card)
                current_card = {}

            elif line.startswith("FRONT:"):
                current_card["front"] = line[6:].strip()

            elif line.startswith("BACK:"):
                current_card["back"] = line[5:].strip()

            elif "front" in current_card and not current_card.get("back"):
                # Continue front text on next line
                current_card["front"] += " " + line

            elif "back" in current_card:
                # Continue back text on next line
                current_card["back"] += " " + line

        # Add the last card
        if current_card.get("front") and current_card.get("back"):
            cards.append(current_card)

        return cards

    def enhance_learning_objective(self, text_preview: str, user_objective: str) -> str:
        """Enhance the user's learning objective with AI suggestions.

        Args:
            text_preview: Preview of the extracted text
            user_objective: User's initial learning objective

        Returns:
            Enhanced learning objective with suggestions
        """
        try:
            prompt = f"""
            Based on this text content preview and the user's learning objective, suggest an enhanced and more specific learning goal.

            TEXT PREVIEW:
            {text_preview[:500]}...

            USER'S OBJECTIVE:
            {user_objective}

            Please provide:
            1. An enhanced, more specific learning objective
            2. 2-3 suggestions for different types of study cards that would be effective
            
            Keep the response concise and practical.
            """

            response = self.model.generate_content(prompt)
            return response.text.strip()

        except Exception as _:
            return user_objective  # Fallback to original objective
