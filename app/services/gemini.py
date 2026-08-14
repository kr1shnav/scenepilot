import json
import os

from dotenv import load_dotenv
from google import genai

load_dotenv()


class GeminiService:
    """
    ScenePilot Gemini API service.

    Uses the Gemini Developer API through Google AI Studio,
    not Vertex AI.
    """

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not configured."
            )

        self.model = os.getenv(
            "GEMINI_MODEL",
            "gemini-2.5-flash",
        )

        self.client = genai.Client(
            api_key=api_key
        )

    async def analyze_screenplay(
        self,
        screenplay_text: str,
    ) -> dict:
        """
        Analyze screenplay and identify scenes.
        """

        prompt = f"""
You are the Script Analyst Agent for ScenePilot.

ScenePilot is an AI film pre-production intelligence
system that converts screenplays into production
intelligence.

Analyze the screenplay and identify every individual
scene.

For each scene extract:

- scene_number
- heading
- location
- interior_exterior
- time_of_day
- summary
- production_requirements
- needs_research
- research_query

Set needs_research=true when external web research
would materially help production planning.

Set needs_research=false when external research would
not meaningfully help.

Research-worthy examples include:

- Real-world locations
- Railway stations
- Airports
- Hotels
- Restaurants
- Landmarks
- National parks
- Cities
- Historical places
- Specific geographical locations
- Real events
- Specialized environments

Return ONLY valid JSON.

Use this structure:

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
                "Railway station",
                "Night lighting",
                "Background crowd"
            ],
            "needs_research": true,
            "research_query": "Research Guwahati Railway Station for film production planning, including location context, environment, access considerations and useful visual details."
        }}
    ]
}}

Do not add markdown.
Do not add explanations.

SCREENPLAY:

{screenplay_text}
"""

        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=prompt,
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
                "Gemini response does not contain a valid scenes list."
            )

        return data

    async def synthesize_production_intelligence(
        self,
        scenes: list[dict],
        research: list[dict],
    ) -> dict:
        """
        Combine screenplay analysis with Parallel research.
        """

        scenes_text = json.dumps(
            scenes,
            indent=2,
            ensure_ascii=False,
        )

        research_text = json.dumps(
            research,
            indent=2,
            ensure_ascii=False,
        )

        prompt = f"""
You are the Production Intelligence Agent for ScenePilot.

Combine:

1. SCREENPLAY ANALYSIS
2. REAL-WORLD RESEARCH FROM PARALLEL

Your job is to produce actionable film
pre-production intelligence.

Do not invent facts.

Only use facts supported by the screenplay
or the provided Parallel research.

Preserve source URLs.

SCREENPLAY ANALYSIS:

{scenes_text}

PARALLEL RESEARCH:

{research_text}

Return ONLY valid JSON.

Use exactly this structure:

{{
    "production_summary": {{
        "total_scenes": 0,
        "researched_scenes": 0,
        "locations": [],
        "major_requirements": [],
        "key_considerations": []
    }},
    "scenes": [
        {{
            "scene_number": 1,
            "heading": "",
            "location": "",
            "summary": "",
            "production_requirements": [],
            "research_findings": [],
            "production_considerations": [],
            "sources": []
        }}
    ]
}}

For every researched scene:

research_findings:
List the useful facts discovered through Parallel.

production_considerations:
Explain what those findings mean for the
film production team.

sources:
Preserve useful source titles and URLs.

Keep the output concise and practical.

Return JSON only.
"""

        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=prompt,
        )

        text = response.text or ""

        if not text:
            raise RuntimeError(
                "Gemini synthesis returned an empty response."
            )

        text = self._clean_json(text)

        try:
            result = json.loads(text)

        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "Gemini synthesis returned invalid JSON."
            ) from exc

        if not isinstance(result, dict):
            raise RuntimeError(
                "Gemini synthesis must return a JSON object."
            )

        return result

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