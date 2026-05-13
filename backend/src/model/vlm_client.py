import os, time, random, base64
from io import BytesIO
import google.generativeai as genai
from groq import Groq
from PIL import Image
from dotenv import load_dotenv

class VLMClient:
    def __init__(self):
        load_dotenv()
        
        # Gemini for vision
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.gemini = genai.GenerativeModel("gemini-2.0-flash")
        
        # Groq for text only
        self.groq = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.groq_model = "llama-3.3-70b-versatile"
        
        self.n_samples = 2
        
        print("VLMClient ready (Decoupled Hybrid Mode)")
        print("  Vision → Gemini 2.5 Flash (direct API)")
        print("  Text   → Groq Llama 3.1 70B (direct API)")

    def generate(self, prompt: str, image_path: str, temperature: float = 0.3) -> str:
        # VISION call — uses Gemini directly
        max_retries = 8
        for attempt in range(max_retries):
            try:
                image = Image.open(image_path).convert("RGB")
                response = self.gemini.generate_content(
                    [prompt, image],
                    generation_config=genai.types.GenerationConfig(
                        temperature=temperature,
                        max_output_tokens=1024
                    )
                )
                print(f"✅ Vision call OK (Gemini) on attempt {attempt+1}")
                return response.text
            except Exception as e:
                if "429" in str(e) or "quota" in str(e).lower() or "exhausted" in str(e).lower():
                    # Standard backoff: 2s, 4s, 8s...
                    wait = 2 * (2 ** attempt) + random.uniform(0, 2)
                    print(f"⚠️ Gemini rate limit hit. Sleeping {wait:.0f}s before attempt {attempt+2}/{max_retries}...")
                    time.sleep(wait)
                else:
                    print(f"❌ Gemini error attempt {attempt+1}: {e}")
                    time.sleep(5)
        
        raise Exception("Gemini API completely blocked after 8 retries. Pipeline halted.")

    def generate_no_image(self, prompt: str, temperature: float = 0.3) -> str:
        # TEXT ONLY call — uses Groq directly
        max_retries = 6
        for attempt in range(max_retries):
            try:
                response = self.groq.chat.completions.create(
                    model=self.groq_model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=1024,
                    temperature=temperature
                )
                print(f"✅ Text call OK (Groq) on attempt {attempt+1}")
                return response.choices[0].message.content
            except Exception as e:
                if "429" in str(e) or "rate_limit" in str(e).lower():
                    # Standard backoff: 1s, 2s, 4s...
                    wait = 1 * (2 ** attempt) + random.uniform(0, 1)
                    print(f"⚠️ Groq rate limit hit. Sleeping {wait:.0f}s before attempt {attempt+2}/{max_retries}...")
                    time.sleep(wait)
                else:
                    print(f"❌ Groq error attempt {attempt+1}: {e}")
                    time.sleep(5)
                    
        raise Exception("Groq API completely blocked after 6 retries. Pipeline halted.")
