from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.schemas.ask import AskRequest, AskResponse
from app.application.use_cases.execute_rag import execute_rag
from app.core.config import get_settings
from app.infrastructure.llm import OpenAIClientError

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    """Verificação simples de disponibilidade do serviço."""
    settings = get_settings()
    return {
        "status": "ok",
        "app": settings.app_name,
    }


@router.post("/ask", response_model=AskResponse)
def ask(
    body: AskRequest,
    db: Session = Depends(get_db),
) -> AskResponse:
    """Executa o cenário solicitado (LLM ou RAG) via caso de uso."""
    try:
        result = execute_rag(db, body.to_execute_input())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except OpenAIClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return AskResponse.from_pipeline(result)
