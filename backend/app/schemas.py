from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str = Field(..., description="Stable per-user/per-tab conversation id")
    area: str = Field(..., description="normativa | edpr | tecnologo")
    question: str
    is_followup: bool = False


class Source(BaseModel):
    archivo: str
    ruta_completa: str
    pagina: str
    score: float | str


class FeedbackRequest(BaseModel):
    session_id: str
    area: str
    question: str
    answer: str
    vote: str  # "POSITIVO" | "NEGATIVO"


class ResetRequest(BaseModel):
    """BUG #13: /api/reset now takes a JSON body instead of a query param."""
    session_id: str
