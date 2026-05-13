from typing import Literal

from pydantic import BaseModel, Field


DebateStyle = Literal["serious", "academic", "sharp", "humorous"]
DebateRole = Literal["affirmative", "negative"]
Winner = Literal["affirmative", "negative", "draw"]


class DebateRequest(BaseModel):
    topic: str = Field(..., min_length=2, max_length=200)
    rounds: int = Field(default=3, ge=1, le=5)
    style: DebateStyle = "serious"


class DebateMessage(BaseModel):
    role: DebateRole
    round: int
    phase: str
    content: str


class JudgeScore(BaseModel):
    affirmative: int = Field(..., ge=0, le=100)
    negative: int = Field(..., ge=0, le=100)


class JudgeResult(BaseModel):
    winner: Winner
    score: JudgeScore
    reason: str
    best_argument: str
    logic_flaws: list[str] = Field(default_factory=list)


class DebateResponse(BaseModel):
    topic: str
    style: DebateStyle
    rounds: int
    messages: list[DebateMessage]
    judge: JudgeResult
    model: str
    mock: bool = False

