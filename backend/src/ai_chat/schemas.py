from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class AIChatRequest(BaseModel):
    campaign_id: int
    messages: List[ChatMessage] = Field(..., description="Conversation history, including the latest user message.")
    # Optional: any other parameters needed for LLM call, like temperature, model preference

class AIChatResponse(BaseModel):
    reply: str # The AI's textual response
    conversation_history: List[ChatMessage] # The updated conversation history

class FinalizeEmailStyleRequest(BaseModel):
    campaign_id: int
    # How to represent the finalized style?
    # Option 1: Pass the entire successful conversation history
    final_conversation: List[ChatMessage]
    # Option 2: Or a specific user-confirmed "final prompt" or "style summary"
    # final_prompt: Optional[str] = None
    # style_parameters: Optional[Dict[str, Any]] = None # If the LLM can output structured style info
    contact_id_for_preview: Optional[int] = None # To generate a sample template

# We can reuse existing EmailTemplateResponse from src.schemas.email_template_schemas
# from src.schemas.email_template_schemas import EmailTemplateResponse
# For now, let's define a simple response for finalization
class FinalizeEmailStyleResponse(BaseModel):
    message: str
    email_template_id: Optional[int] = None # ID of the created EmailTemplate
    preview_subject: Optional[str] = None
    preview_body: Optional[str] = None

    class Config:
        from_attributes = True # Pydantic V2 style for orm_mode
        # orm_mode = True # Pydantic V1 style
