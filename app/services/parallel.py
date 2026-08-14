import os
from typing import Any

from dotenv import load_dotenv
from parallel import Parallel

load_dotenv()


class ParallelService:
    """Research screenplay scenes with the Parallel API."""

    def __init__(self) -> None:
        api_key = os.getenv("PARALLEL_API_KEY")

        if not api_key:
            raise RuntimeError(
                "PARALLEL_API_KEY is not configured."
            )

        self.client = Parallel(api_key=api_key)

        self.processor = os.getenv(
            "PARALLEL_PROCESSOR",
            "core",
        )

    def research_scene(
        self,
        scene: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Research one screenplay scene using Parallel.
        """

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

Research the following screenplay scene for a filmmaker.

Use reliable current web sources.
Do not invent facts.

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

Find information that can materially help a
film production team.

Focus on:

- Real-world location facts
- Location context
- Environmental or geographical information
- Access or filming considerations when available
- Visual/contextual details
- Logistical considerations
- Relevant restrictions
- Timing considerations
- Practical production considerations

Return concise findings with supporting sources.
"""

        # Parallel's execute method creates the task,
        # waits for completion, and returns the result.
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

        sources: list[dict[str, Any]] = []

        # Parallel returns citation information through
        # the output basis.
        for basis in getattr(
            output,
            "basis",
            [],
        ) or []:

            for citation in getattr(
                basis,
                "citations",
                [],
            ) or []:

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
        unique_sources: list[
            dict[str, Any]
        ] = []

        seen_urls: set[str] = set()

        for source in sources:
            url = source.get("url")

            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_sources.append(source)

        return {
            "status": "completed",
            "processor": self.processor,
            "content": content,
            "sources": unique_sources,
        }