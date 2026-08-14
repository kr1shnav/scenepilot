import json

from google import genai

from app.config import settings


class GeminiService:

    def __init__(self):
        self.client = genai.Client()

    async def analyze_screenplay(
        self,
        screenplay_text: str,
    ) -> dict:
        """
        Analyze screenplay and return structured scene data.
        """

        prompt = f"""
You are the Script Analyst Agent for ScenePilot.

ScenePilot is an AI film pre-production intelligence
system that converts screenplays into production
intelligence.

Analyze the screenplay and identify every individual
scene.

For each scene extract:

1. Scene number
2. Full scene heading
3. Location
4. Interior or exterior
5. Time of day
6. Short summary
7. Important production requirements
8. Whether external web research would materially
   improve production planning
9. A concise research query when research is useful

IMPORTANT:

Set "needs_research" to true when the scene contains
a real-world location, landmark, geographical setting,
specific venue, historical setting, environmental
condition, transportation setting, or other detail
where external information would help a filmmaker.

Set "needs_research" to false for scenes where external
research would not add meaningful production value.

If a screenplay contains at least one specific
real-world location, make sure that scene has
"needs_research": true.

Return ONLY valid JSON.

Use exactly this structure:

{{
    "scenes": [
        {{
            "scene_number": 1,
            "heading": "EXT. GUWAHATI RAILWAY STATION - NIGHT",
            "location": "Guwahati Railway Station",
            "interior_exterior": "EXT",
            "time_of_day": "NIGHT",
            "summary": "A character waits on the platform.",
            "production_requirements": [
                "Railway station location",
                "Night lighting",
                "Background crowd"
            ],
            "needs_research": true,
            "research_query": "Research Guwahati Railway Station for film production planning, including location context, environment, access considerations, and useful visual details."
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

        text = response.text or ""

        if not text:
            raise RuntimeError(
                "Gemini returned an empty response."
            )

        # Remove accidental markdown fences.
        text = text.strip()

        if text.startswith("```json"):
            text = text[7:]

        elif text.startswith("```"):
            text = text[3:]

        if text.endswith("```"):
            text = text[:-3]

        text = text.strip()

        try:
            data = json.loads(text)

        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "Gemini returned invalid JSON."
            ) from exc

        if not isinstance(data, dict):
            raise RuntimeError(
                "Gemini response must be a JSON object."
            )

        scenes = data.get("scenes")

        if not isinstance(scenes, list):
            raise RuntimeError(
                "Gemini response does not contain a valid scenes list."
            )

        return data