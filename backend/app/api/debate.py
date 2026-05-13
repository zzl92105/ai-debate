from fastapi import APIRouter, Depends, HTTPException

from app.schemas.debate import DebateRequest, DebateResponse
from app.services.debate_service import DebateService, get_debate_service

router = APIRouter(tags=["debate"])


@router.post("/debate/run", response_model=DebateResponse)
async def run_debate(
    request: DebateRequest,
    service: DebateService = Depends(get_debate_service),
) -> DebateResponse:
    try:
        return await service.run(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Debate generation failed: {exc}") from exc

