from fastapi import APIRouter, HTTPException
from app.models.chat import ChatRequest, ChatResponse
from app.services.nlp_service import NLPService
from app.services.response_service import ResponseService

router = APIRouter(prefix="/api/chat", tags=["Chat"])

nlp_service = NLPService()
response_service = ResponseService()

@router.post("/", response_model=ChatResponse)
async def chat_with_bot(request: ChatRequest):
    try:
        nlp_result = await nlp_service.analyze_message(request.message)
        reply = await response_service.generate_response(nlp_result, request.message)
        return ChatResponse(response=reply)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
