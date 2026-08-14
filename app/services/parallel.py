import os
from typing import Any

from dotenv import load_dotenv
from parallel import Parallel

load_dotenv()


class ParallelService:
    """
    ScenePilot Parallel research service.
    """

    def __init__(self) -> None:
        api_key = os.getenv(
            "PARALLEL_API_KEY"
        )

        if not api_key:
            raise RuntimeError(
                "PARALLEL_API_KEY is not configured."
            )

        self.client = Parallel(
            api_key=api_key
        )

        self.processor = os.getenv(
            "PARALLEL_PROCESSOR",
            "core",
        )

    def research_scene(
        self,
        scene: dict[str, Any],
    ) -> dict[str, Any]:

        heading = scene.get(
            "heading",
            "Unknown scene",
        )

        location = scene.get(
            "location",
            "Unknown location",
        )

        summary = scene.get(
            "summary",
            "",
        )

        requirements = scene.get(
            "production_requirements",
            [],
        )

        research_query = scene.get(
            "research_query",
            "",
        )

        objective = f"""
You are the web research specialist for ScenePilot,
an AI film pre-production intelligence system.

Research this screenplay scene for a filmmaker.

SCENE HEADING:
{heading}

LOCATION:
{location}

SCENE SUMMARY:
{summary}

PRODUCTION REQUIREMENTS:
{requirements}

RESEARCH FOCUS:
{research_query}

Find useful, factual information that can help a
film production team.

Focus on:

- Real-world location facts
- Location context
- Geography
- Environment
- Access considerations
- Visual details
- Logistics
- Restrictions
- Timing considerations
- Practical filming considerations

Do not invent facts.

Use reliable web sources.

Return concise findings with supporting sources.
"""

        result = self.client.task_run.execute(
            processor=self.processor,
            input=objective,
        )

        output = result.output

        content = getattr(
            output,
            "content",
            None,
        )

        if content is None:
            content = str(output)

        sources = []

        for basis in (
            getattr(
                output,
                "basis",
                [],
            )
            or []
        ):

            for citation in (
                getattr(
                    basis,
                    "citations",
                    [],
                )
                or []
            ):

                sources.append(
                    {
                        "title": getattr(
                            citation,
                            "title",
                            None,
                        ),
                        "url": getattr(
                            citation,
                            "url",
                            None,
                        ),
                        "excerpts": getattr(
                            citation,
                            "excerpts",
                            None,
                        ),
                    }
                )

        # Remove duplicate URLs.
        unique_sources = []
        seen_urls = set()

        for source in sources:

            url = source.get("url")

            if url and url not in seen_urls:

                seen_urls.add(url)

                unique_sources.append(
                    source
                )

        return {
            "status": "completed",
            "processor": self.processor,
            "content": content,
            "sources": unique_sources,
        }