from pydantic import BaseModel, Field


class Scene(BaseModel):
    scene_number: int = Field(
        description="Sequential scene number"
    )

    heading: str = Field(
        description="Full screenplay scene heading"
    )

    location: str = Field(
        description="Primary location of the scene"
    )

    interior_exterior: str = Field(
        description="Whether the scene is INT, EXT, or INT/EXT"
    )

    time_of_day: str = Field(
        description="Time of day such as DAY, NIGHT, MORNING, SUNSET"
    )

    summary: str = Field(
        description="Short summary of what happens in the scene"
    )

    production_requirements: list[str] = Field(
        default_factory=list,
        description="Important production requirements for the scene"
    )