import asyncio
import json
import os

from dotenv import load_dotenv
from google import genai

load_dotenv()


class GeminiService:
    """
    ScenePilot Gemini service.

    IMPORTANT:
    This service intentionally performs only ONE Gemini
    request per screenplay analysis.

    Production synthesis is handled locally after
    Parallel research to reduce Gemini quota usage.
    """

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not configured."
            )

        self.model = os.getenv(
            "GEMINI_MODEL",
            "gemini-3.5-flash",
        )

        self.client = genai.Client(
            api_key=api_key
        )

    async def _generate(
        self,
        prompt: str,
        retries: int = 2,
    ):
        """
        Generate Gemini content.

        IMPORTANT:
        429 quota errors are NOT retried.

        Retrying a daily quota error wastes time and
        does not increase the available quota.
        """

        last_error = None

        for attempt in range(retries):

            try:
                return await (
                    self.client
                    .aio
                    .models
                    .generate_content(
                        model=self.model,
                        contents=prompt,
                    )
                )

            except Exception as exc:

                last_error = exc
                error_text = str(exc).upper()

                # Never retry quota exhaustion.
                if (
                    "429" in error_text
                    or "RESOURCE_EXHAUSTED" in error_text
                    or "QUOTA" in error_text
                ):
                    raise

                retryable = any(
                    code in error_text
                    for code in [
                        "503",
                        "UNAVAILABLE",
                        "500",
                        "INTERNAL",
                    ]
                )

                if not retryable:
                    raise

                if attempt >= retries - 1:
                    raise

                delay = 2 ** (attempt + 1)

                print(
                    f"Gemini temporary error. "
                    f"Retrying in {delay}s..."
                )

                await asyncio.sleep(delay)

        raise last_error

    async def analyze_screenplay(
        self,
        screenplay_text: str,
    ) -> dict:
        """
        ONE Gemini request.

        Extract all scenes and determine which scenes
        should be researched by Parallel.
        """

        prompt = f"""
You are the Script Analyst Agent for ScenePilot.

ScenePilot converts screenplays into practical
film pre-production intelligence.

Analyze the screenplay below.

Identify EVERY individual scene.

For each scene return:

- scene_number
- heading
- location
- interior_exterior
- time_of_day
- summary
- production_requirements
- needs_research
- research_query

Set needs_research=true ONLY when external research
would materially help a film production team.

Research-worthy examples:

- Real-world locations
- Railway stations
- Airports
- Hotels
- Restaurants
- Landmarks
- National parks
- Cities
- Historical locations
- Geographical locations
- Real events
- Specialized environments
- Places with filming restrictions
- Places where weather/access/safety matters

For ordinary fictional interiors such as:
"SMALL APARTMENT"
do not request external research unless the
screenplay provides a specific real location.

Be concise.

Do NOT invent facts.

Return ONLY valid JSON.

Use exactly:

{{
    "scenes": [
        {{
            "scene_number": 1,
            "heading": "EXT. LOCATION - NIGHT",
            "location": "Location",
            "interior_exterior": "EXT",
            "time_of_day": "NIGHT",
            "summary": "Short scene summary.",
            "production_requirements": [
                "Requirement 1",
                "Requirement 2"
            ],
            "needs_research": true,
            "research_query": "Specific research objective for Parallel."
        }}
    ]
}}

Do not use Markdown.
Do not use ```json.
Do not add explanations.

SCREENPLAY:

{screenplay_text}
"""

        response = await self._generate(
            prompt,
            retries=2,
        )

        text = response.text or ""

        if not text:
            raise RuntimeError(
                "Gemini returned an empty response."
            )

        text = self._clean_json(text)

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
                "Gemini response does not contain "
                "a valid scenes list."
            )

        return data

    @staticmethod
    def _clean_json(text: str) -> str:
        """
        Remove accidental Markdown code fences.
        """

        text = text.strip()

        if text.startswith("```json"):
            text = text[7:]

        elif text.startswith("```"):
            text = text[3:]

        if text.endswith("```"):
            text = text[:-3]

        return text.strip()