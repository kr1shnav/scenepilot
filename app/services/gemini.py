from google import genai

from app.config import settings


class GeminiService:

    def __init__(self):
        self.client = genai.Client()

    async def analyze_screenplay(
        self,
        screenplay_text: str,
    ) -> str:

        prompt = f"""
You are the Script Analyst Agent for ScenePilot.

ScenePilot is an AI film pre-production system.

Your job is to analyze a screenplay and identify
every individual scene.

For each scene extract:

1. Scene number
2. Full scene heading
3. Location
4. Interior or exterior
5. Time of day
6. Short summary
7. Important production requirements

Return ONLY valid JSON.

Use exactly this structure:

{{
    "scenes": [
        {{
            "scene_number": 1,
            "heading": "EXT. BEACH - SUNSET",
            "location": "Beach",
            "interior_exterior": "EXT",
            "time_of_day": "SUNSET",
            "summary": "A character walks along the beach.",
            "production_requirements": [
                "Beach location",
                "Sunset lighting"
            ]
        }}
    ]
}}

Do not add markdown.
Do not add explanations.

SCREENPLAY:

{screenplay_text}
"""

        response = await self.client.aio.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
        )

        return response.text or ""