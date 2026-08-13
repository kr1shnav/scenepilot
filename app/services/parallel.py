import os
import time
from typing import Any

from dotenv import load_dotenv
from parallel import Parallel

load_dotenv()


class ParallelService:
    """
    ScenePilot integration with the Parallel API.

    Parallel is used to research real-world information relevant
    to screenplay scenes and return research that can later be
    synthesized by Gemini.
    """

    def __init__(self) -> None:
        api_key = os.getenv("PARALLEL_API_KEY")

        if not api_key:
            raise RuntimeError(
                "PARALLEL_API_KEY is not configured."
            )

        self.client = Parallel(api_key=api_key)

    def research_scene(
        self,
        scene_description: str,
    ) -> Any:
        """
        Research a screenplay scene using Parallel.

        This creates a Parallel task, waits for completion,
        and returns the completed task information.
        """

        if not scene_description.strip():
            raise ValueError(
                "scene_description cannot be empty."
            )

        objective = f"""
You are researching a film production scene.

Analyze the following screenplay scene and find useful,
fact-based information that can help a filmmaker plan
and understand the scene.

SCREENPLAY SCENE:
{scene_description}

RESEARCH OBJECTIVES:

1. Identify important real-world location information.
2. Find relevant environmental or geographical context.
3. Identify production considerations.
4. Identify logistical considerations.
5. Find useful visual/contextual information.
6. Identify information that could affect filming.
7. Provide reliable sources for important claims.

Focus on information that is genuinely useful to a
film production team.

Do not invent facts.

Return concise, useful research with source information.
"""

        task = self.client.task_run.create(
            processor="core",
            input=objective,
        )

        run_id = task.run_id

        # Poll until Parallel finishes the research task.
        while True:
            result = self.client.task_run.retrieve(run_id)

            if result.status == "completed":
                return result

            if result.status == "failed":
                error = result.error or "Unknown Parallel error"

                raise RuntimeError(
                    f"Parallel research failed: {error}"
                )

            time.sleep(2)