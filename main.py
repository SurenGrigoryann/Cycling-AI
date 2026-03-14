import base64
import io
import json
import os

import anthropic
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from PIL import Image
from starlette.requests import Request

load_dotenv()

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """You are a friendly recycling helper for young children aged 6-10.
When shown a photo of an item, respond ONLY with valid JSON in this exact format:
{
  "item": "short name of the item",
  "bin": "recycling" or "plastic" or "garbage",
  "reason": "one simple sentence explaining why, using words a 6-year-old understands",
  "emoji": "one relevant emoji for the item"
}

Bin definitions:
- "recycling": paper, cardboard, glass bottles/jars, metal cans, aluminum foil
- "plastic": plastic bottles, plastic containers, plastic bags, plastic packaging, plastic toys
- "garbage": food waste, tissues, dirty napkins, broken items that can't be recycled, mixed materials

Always be encouraging and positive. Never say anything scary or complicated.
If you cannot identify an item clearly, use "garbage" as a safe default.
Respond ONLY with the JSON object, no other text."""


def resize_image(image_bytes: bytes, max_size: int = 1024) -> bytes:
    img = Image.open(io.BytesIO(image_bytes))
    img.thumbnail((max_size, max_size), Image.LANCZOS)
    if img.mode != "RGB":
        img = img.convert("RGB")
    output = io.BytesIO()
    img.save(output, format="JPEG", quality=85)
    return output.getvalue()


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    image_bytes = await file.read()

    # Resize to keep under API limits
    try:
        image_bytes = resize_image(image_bytes)
    except Exception:
        raise HTTPException(status_code=400, detail="Could not process image")

    image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

    try:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=300,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": image_b64,
                            },
                        },
                        {
                            "type": "text",
                            "text": "What item is it?",
                        },
                    ],
                }
            ],
        )

        response_text = message.content[0].text.strip()

        # Strip markdown code fences if present
        if response_text.startswith("```"):
            lines = response_text.splitlines()
            response_text = "\n".join(
                line for line in lines if not line.startswith("```")
            ).strip()

        result = json.loads(response_text)

        # Validate bin value
        # if result.get("bin") not in ("recycling", "plastic", "garbage"):
        #     result["bin"] = "garbage"

        return result

    except json.JSONDecodeError:
        return {
            "item": "unknown item",
            "bin": "garbage",
            "reason": "I couldn't quite tell what that is — when not sure, use the garbage bin!",
            "emoji": "🗑️",
        }
    except anthropic.APIError as e:
        raise HTTPException(status_code=502, detail=f"AI service error: {str(e)}")
