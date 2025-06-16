from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.auth.dependencies import get_current_active_user
from src.schemas.user_schemas import User as UserSchemaModel # Pydantic User schema
from .service import AIChatService
from .schemas import (
    ChatMessage,
    AIChatRequest,
    AIChatResponse,
    FinalizeEmailStyleRequest,
    FinalizeEmailStyleResponse, # Import the updated response model
)
# from src.schemas.email_template_schemas import EmailTemplateResponse # No longer needed here if FinalizeEmailStyleResponse is self-contained or inherits


router = APIRouter(
    prefix="/api/v1/ai-chat",
    tags=["AI Chat & Email Style"]
)

# Placeholder for AIChatService instance
chat_service = AIChatService()

@router.post("/conversation", response_model=AIChatResponse)
async def handle_chat_message(
    request: AIChatRequest,
    db: Session = Depends(get_db),
    current_user: UserSchemaModel = Depends(get_current_active_user) # Changed to UserSchemaModel
):
    try:
        ai_reply_content = await chat_service.process_chat_interaction(
            db=db,
            campaign_id=request.campaign_id,
            conversation_history=request.messages,
            current_user=current_user # This is UserSchemaModel, service handles fetching ORM
        )

        updated_history = request.messages + [ChatMessage(role="assistant", content=ai_reply_content)]
        return AIChatResponse(reply=ai_reply_content, conversation_history=updated_history)
    except ValueError as ve: # Example: campaign not found or auth issue from service layer
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        # Log the exception e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred during chat processing.")


@router.post("/finalize-style", response_model=FinalizeEmailStyleResponse) # NEW response model
async def finalize_email_style(
    request: FinalizeEmailStyleRequest,
    db: Session = Depends(get_db),
    current_user: UserSchemaModel = Depends(get_current_active_user) # UserSchemaModel from Pydantic
):
    try:
        result_data = await chat_service.finalize_style_and_create_template(
            db=db,
            campaign_id=request.campaign_id,
            final_conversation_history=request.final_conversation,
            current_user_schema=current_user,
            contact_id_for_preview=request.contact_id_for_preview
        )

        email_template_orm = result_data["email_template"]

        # Construct FinalizeEmailStyleResponse.
        # If FinalizeEmailStyleResponse was designed to inherit from an EmailTemplate schema
        # that uses from_orm, this could be more direct.
        # For now, manual construction based on its fields.
        return FinalizeEmailStyleResponse(
            message="Successfully finalized style and created template.",
            email_template_id=email_template_orm.id,
            preview_subject=result_data["preview_subject"],
            preview_body=result_data["preview_body"]
            # If FinalizeEmailStyleResponse is also meant to include full template details,
            # those would need to be mapped here from email_template_orm as well,
            # e.g., subject_template=email_template_orm.subject_template, etc.
            # Or it should inherit from a base Pydantic model that does this via from_orm.
            # The current FinalizeEmailStyleResponse is minimal.
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e: # Catch-all for unexpected errors
        # Log error e (e.g., import logging; logging.error(f"Finalize style error: {e}", exc_info=True))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred during style finalization.")
