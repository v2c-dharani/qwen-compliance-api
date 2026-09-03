import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from app.schemas import ChatCompletionRequest, ChatCompletionResponse, HealthResponse, ErrorResponse
from app.auth import verify_api_key
from app.model import QwenModelService

load_dotenv()

# Configure structured logging (Never log secret API keys)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("qwen_api.main")

# Singleton instance of model service
model_service = QwenModelService()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan handler: loads the model once when server starts,
    preserving it in memory for all subsequent requests.
    """
    logger.info("Starting up FastAPI Qwen Model Server...")
    try:
        model_service.load_model()
    except Exception as e:
        logger.error(f"Critical error during model startup: {e}")
        raise e
    yield
    logger.info("Shutting down Qwen Model Server...")

app = FastAPI(
    title="Fine-Tuned Qwen Compliance API",
    description="Local REST API for serving fine-tuned Qwen2.5-1.5B-Instruct cybersecurity compliance model.",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS for multi-website access
allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "*")
allowed_origins = [origin.strip() for origin in allowed_origins_str.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception Handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "detail": exc.detail}
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Internal server error processing request: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"success": False, "detail": "An internal server error occurred while processing the request."}
    )

@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Health check endpoint (No API Key required)"
)
async def health_check():
    """
    Health check endpoint to verify server status and model identity.
    Does not require API Key authentication.
    """
    return HealthResponse(
        status="ok",
        model=os.getenv("MODEL_NAME", "qwen-compliance")
    )

@app.post(
    "/v1/chat",
    response_model=ChatCompletionResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request parameters"},
        401: {"model": ErrorResponse, "description": "Missing or invalid API key"},
        500: {"model": ErrorResponse, "description": "Model generation failure"}
    },
    tags=["Chat"],
    summary="Submit question to local fine-tuned Qwen model (POST /v1/chat)"
)
@app.post(
    "/v1/chat/completions",
    response_model=ChatCompletionResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request parameters"},
        401: {"model": ErrorResponse, "description": "Missing or invalid API key"},
        500: {"model": ErrorResponse, "description": "Model generation failure"}
    },
    tags=["Chat"],
    summary="Submit question to local fine-tuned Qwen model (POST /v1/chat/completions)"
)
async def chat_completions(
    request: ChatCompletionRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Receives user compliance questions, forwards them to the in-memory fine-tuned Qwen model,
    and returns JSON {"response": "AI output text here"}.
    Requires header: X-API-Key or Authorization: Bearer <key>
    """
    if not request.message or not request.message.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request message cannot be empty."
        )

    logger.info(f"Processing compliance query (Length: {len(request.message.strip())} chars)")

    try:
        answer = model_service.generate_answer(user_message=request.message.strip())
        logger.info("Compliance response generated successfully.")
        return ChatCompletionResponse(response=answer, success=True, answer=answer)
    except Exception as e:
        logger.error(f"Model generation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate answer from local model: {str(e)}"
        )
