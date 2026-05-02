import os
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image

# Load environment variables
load_dotenv()

# Configure Gemini API
gemini_api_key = os.getenv("GEMINI_API_KEY")
if gemini_api_key:
    genai.configure(api_key=gemini_api_key)
else:
    print("Warning: GEMINI_API_KEY not found in environment variables.")

class VLMClient:
    def __init__(self):
        # We use gemini-2.5-flash as requested
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    def generate(self, prompt: str, image_path: str, temperature: float = 0.3) -> str:
        """
        Opens an image, converts it to RGB, and sends it along with the prompt
        to the Gemini 1.5 Flash model.

        Parameters
        ----------
        prompt : str
            Text prompt to send alongside the image.
        image_path : str
            Path to the chest X-ray image.
        temperature : float
            Sampling temperature (default 0.3 for deterministic generation;
            use higher values e.g. 0.7 for uncertainty sampling).
        """
        # Open and convert image
        try:
            image = Image.open(image_path).convert("RGB")
        except Exception as e:
            raise RuntimeError(f"Failed to open image at {image_path}: {e}")

        # Generation config — temperature is now dynamic
        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=1024,
        )

        # Send request
        response = self.model.generate_content(
            [prompt, image],
            generation_config=generation_config
        )

        return response.text
