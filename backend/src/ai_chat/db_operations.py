# backend/src/ai_chat/db_operations.py
from sqlalchemy.orm import Session
from sqlalchemy import update
from typing import Optional

from src.models.email_template_models import EmailTemplate
from src.schemas.email_template_schemas import EmailTemplateCreate

async def db_set_other_templates_not_primary(
    db: Session,
    campaign_id: int,
    new_template_id: Optional[int] = None
):
    """
    Sets is_primary = False for all templates in the campaign,
    optionally excluding a specific new_template_id that will become primary.
    """
    stmt = (
        update(EmailTemplate)
        .where(EmailTemplate.campaign_id == campaign_id)
        .values(is_primary=False)
    )
    if new_template_id:
        # This condition ensures that if the new_template_id was somehow already primary,
        # it's not accidentally set to False. Typically, a new template won't be in DB yet.
        # For existing templates being promoted, this is more relevant.
        # Given our flow (new template becomes primary), this is a safeguard.
        stmt = stmt.where(EmailTemplate.id != new_template_id)

    await db.execute(stmt)
    # No commit here, assume calling function handles transaction
