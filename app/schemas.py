from pydantic import BaseModel, Field

class ChatCompletionRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        description="The prompt or question to send to the Qwen compliance model.",
        examples=["What is NIST SP 800-53?"]
    )

class ChatCompletionResponse(BaseModel):
    response: str
    success: bool = True
    answer: str

class HealthResponse(BaseModel):
    status: str = "ok"
    model: str = "qwen-compliance"

class ErrorResponse(BaseModel):
    success: bool = False
    detail: str
