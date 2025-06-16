# backend/src/llm/email_generator.py
import os
import json # For potential structured output from LLM
from typing import Dict, Tuple, Optional, List, Any

from src.ai_chat.schemas import ChatMessage

# Placeholder for actual LLM client library (e.g., from openai import OpenAI)
# For this subtask, we'll simulate the interaction.

# It's crucial to load API keys from environment variables or a secure config system.
# NEVER hardcode API keys.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# from openai import OpenAI # Ensure this import is uncommented when using actual API

# Assuming User ORM model is importable for type hinting
from src.models.user_models import User as UserORMModel


class LLMIntegrationError(Exception):
    """Custom exception for LLM integration issues."""
    pass

def _construct_llm_prompt(
    user_core_prompt: str,
    contact_data: Dict[str, str],
    current_user: UserORMModel, # Changed type hint
    is_template_generation: bool = False # New parameter
) -> str:
    """
    Constructs a detailed prompt for the LLM.
    If is_template_generation is True, instructs LLM to use placeholders.
    Otherwise, instructs LLM to use contact_data for personalization.
    """
    user_full_name = current_user.full_name if hasattr(current_user, 'full_name') else "a team member"
    # Safely access user_company_name and user_role, providing defaults if not present
    user_company_name = getattr(current_user, 'user_company_name', "your company")
    user_role = getattr(current_user, 'user_role', None)

    sender_intro = f"The email is from {user_full_name}"
    if user_role:
        sender_intro += f", {user_role}"
    sender_intro += f" at {user_company_name}."

    if is_template_generation:
        template_instructions = (
            "You are generating an email template. Use placeholders like {{first_name}}, "
            "{{company_name}}, {{job_title}}, etc., for any contact-specific information. "
            "The final output should be a generic template that can be personalized later."
        )
        guidance_on_placeholders = "Ensure you use placeholders like {{first_name}}, {{company_name}} etc."
        contact_data_section_header = "### Example Contact Data for Context (use placeholders in output):\n"
        if not contact_data: # If no contact data, guide to use generic placeholders
             contact_data_section_header = "### Contact Data for Personalization: (No specific contact provided for this template generation, use generic placeholders where appropriate.)\n"
    else:
        template_instructions = (
            "You are generating a specific email for the provided contact. "
            "Do not use placeholders like {{first_name}}; instead, use the actual values "
            "provided in the contact data for personalization."
        )
        guidance_on_placeholders = "Use the actual contact data values, not placeholders like {{first_name}}."
        contact_data_section_header = "### Contact Data for Personalization:\n"

    system_message = (
        "You are an expert marketing assistant. Your task is to write a professional, concise, and engaging "
        f"outreach email. {template_instructions} "
        "Generate a suitable subject line and the email body. Ensure the tone is appropriate for a first contact. "
        f"{sender_intro}"
    )

    contact_context = contact_data_section_header
    if contact_data:
        for key, value in contact_data.items():
            contact_context += f"- {key.replace('_', ' ').title()}: {value}\n"
    elif is_template_generation : # Add example placeholders if generating template and no contact data
        contact_context += "- First Name: {{first_name}}\n- Company Name: {{company_name}}\n- Job Title: {{job_title}}\n"


    full_prompt = f"""
{system_message}

### User's Core Request:
{user_core_prompt}

{contact_context}

### Your Task:
Based on the user's request and contact data (if provided for context or example), generate:
1. A compelling subject line (label it as 'Subject:').
2. The full email body (label it as 'Body:').
{guidance_on_placeholders}
"""
    return full_prompt


async def generate_personalized_email(
    user_core_prompt: str,
    contact_data: Dict[str, str], # e.g., {"first_name": "John", "company_name": "Acme Corp", ...}
    current_user: UserORMModel, # Changed type hint
    is_template_generation: bool = False, # New parameter
    api_key: Optional[str] = None
) -> Tuple[str, str]:
    """
    Generates a personalized email subject and body using an LLM.

    Args:
        user_core_prompt: The user's high-level instruction for the email.
        contact_data: A dictionary containing personalization data for the contact.
        current_user: The ORM model instance of the authenticated user sending the email.
        api_key: The LLM API key. If None, it will try to use a pre-configured key (e.g., env var).

    Returns:
        A tuple (subject, body).

    Raises:
        LLMIntegrationError: If there's an issue with the LLM API call or response.
    """

    # In a real app, api_key would be fetched securely if not provided.
    current_api_key = api_key or OPENAI_API_KEY
    if not current_api_key:
        print("Warning: OPENAI_API_KEY not found. Using simulated LLM response.")
        # Pass is_template_generation to simulation too, if it needs to adapt
        return _simulate_llm_response(user_core_prompt, contact_data, current_user, is_template_generation)

    # client = OpenAI(api_key=current_api_key) # Uncomment when using actual API

    prompt_to_llm = _construct_llm_prompt(
        user_core_prompt,
        contact_data,
        current_user,
        is_template_generation=is_template_generation # Pass it through
    )

    print("\n--- Attempting LLM API Call (Commented Out) ---")
    # print(f"Generated Prompt for LLM:\n{prompt_to_llm}") # For debugging, can be very verbose
    print(f"Prompt constructed. Length: {len(prompt_to_llm)}")
    print("------------------------------------\n")

    generated_text = ""
    # === Example of actual LLM API call (Commented Out) ===
    # try:
    #     # Ensure you have the 'openai' library installed: pip install openai
    #     # And initialize the client: client = OpenAI(api_key=current_api_key)
    #     response = client.chat.completions.create(
    #         model="gpt-3.5-turbo",  # Or your preferred model, e.g., "gpt-4"
    #         messages=[
    #             {"role": "user", "content": prompt_to_llm}
    #         ],
    #         temperature=0.7,  # Adjust for creativity
    #         max_tokens=500,   # Adjust based on expected output length
    #         # You might want to add other parameters like 'n' for multiple choices, 'stop' sequences, etc.
    #     )
    #     generated_text = response.choices[0].message.content.strip()
    #     if not generated_text:
    #         raise LLMIntegrationError("LLM returned an empty response.")
    # except Exception as e:
    #     # Log the error for debugging purposes
    #     print(f"LLM API call error: {e}") # Consider using proper logging
    #     # Depending on the error, you might want to retry or use a fallback.
    #     print("Falling back to simulated LLM response due to (simulated) API error.")
    #     return _simulate_llm_response(user_core_prompt, contact_data, current_user)
    # =======================================================

    # If the actual API call is commented out, we must use simulation:
    if not generated_text: # This will be true if the above block is commented out
        print("Using simulated LLM response as the API call block is commented out.")
        return _simulate_llm_response(user_core_prompt, contact_data, current_user, is_template_generation)

    # --- Parse the generated text to extract subject and body ---
    subject = "Default Subject - Check LLM Output"
    body = "Default Body - Check LLM Output"

    lines = generated_text.split('\n')
    body_lines = []
    parsing_body = False

    for line in lines:
        if line.lower().startswith("subject:"):
            subject = line.split(":", 1)[1].strip()
            parsing_body = False # Reset if subject is encountered again
        elif line.lower().startswith("body:"):
            body_lines.append(line.split(":", 1)[1].strip()) # Add the rest of the "Body:" line
            parsing_body = True
        elif parsing_body:
            body_lines.append(line)

    if body_lines:
        body = "\n".join(body_lines).strip()
    elif "Default Subject" in subject and not body_lines : # Fallback if only subject was found, and no "Body:" tag
         # Try to take everything after the subject line as body
        subject_found = False
        temp_body_lines = []
        for line in lines:
            if line.lower().startswith("subject:"):
                subject_found = True
                continue
            if subject_found:
                temp_body_lines.append(line)
        if temp_body_lines:
            body = "\n".join(temp_body_lines).strip()


    # If still default, do a simpler parse (less reliable)
    if "Default Subject" in subject and "Default Body" in body:
        if lines and lines[0].lower().startswith("subject:"):
             subject = lines[0].split(":", 1)[1].strip()
             if len(lines) > 1 and lines[1].lower().startswith("body:"):
                 body = "\n".join(l.split(":",1)[1] if i==0 else l for i,l in enumerate(lines[1:])).strip() # Complicated
             elif len(lines) > 1 :
                 body = "\n".join(lines[1:]).strip()

        elif lines and len(lines) > 1 : # Assume first non-empty line is subject, rest is body
            first_line = lines[0].strip()
            if first_line :
                subject = first_line
                body = "\n".join(lines[1:]).strip()


    return subject, body


def _simulate_llm_response(user_core_prompt: str, contact_data: Dict[str, str], current_user: UserORMModel, is_template_generation: bool = False) -> Tuple[str, str]:
    """Provides a simulated LLM response for testing."""
    user_full_name = current_user.full_name if hasattr(current_user, 'full_name') else "[Sender Name]"
    # Safely access user_company_name and user_role for simulation context
    user_company_name = getattr(current_user, 'user_company_name', "Your Company")
    user_role = getattr(current_user, 'user_role', None)

    sender_signature_name = user_full_name
    sender_signature_details = f"{user_role}, {user_company_name}" if user_role else user_company_name


    print(f"Simulating LLM response for contact: {contact_data.get('email', 'N/A') if not is_template_generation else 'template generation'}, from user: {user_full_name}")

    if is_template_generation:
        subject = f"Template: {user_core_prompt[:20]}... for {{company_name}}"
        body = f"""Hi {{first_name}},

I hope this email finds you well.

I'm {user_full_name}, writing to you from {user_company_name}. We are reaching out to companies like {{company_name}} regarding their work in {{industry_placeholder}}.

My core message is about: "{user_core_prompt}". We believe our solutions in this area could be highly beneficial for you.

Would you be available for a brief 15-minute chat next week to discuss how {user_company_name} can specifically help your team?

Best regards,
{sender_signature_name}
{sender_signature_details}
"""
    else:
        subject = f"Regarding {user_core_prompt[:20]}... for {contact_data.get('company_name', 'your company')}"
        body = f"""Hi {contact_data.get('first_name', 'Valued Professional')},

I hope this email finds you well.

I'm {user_full_name}, writing to you from {user_company_name}. We noticed your work at {contact_data.get('company_name', 'your company')} and were particularly interested in your role as {contact_data.get('job_title', 'a key player in your industry')}.

My core message is about: "{user_core_prompt}". We believe our solutions in this area could be highly beneficial for you.

Would you be available for a brief 15-minute chat next week to discuss how {user_company_name} can specifically help {contact_data.get('company_name', 'your team')}?

Best regards,
{sender_signature_name}
{sender_signature_details}
"""
    return subject, body


async def generate_chat_response(
    conversation_history: List[ChatMessage],
    current_user: UserORMModel, # Changed type hint
    campaign_id: int,
    # contact_data_for_llm: Optional[Dict[str, str]] = None # Not used in this basic chat simulation
    api_key: Optional[str] = None
) -> str:
    """
    Generates a chat response using an LLM based on the conversation history.
    Prepends a system message if not already present.
    """
    current_api_key = api_key or OPENAI_API_KEY
    if not current_api_key:
        print("Warning: OPENAI_API_KEY not found. Using simulated LLM chat response.")
        # Simulate a chat response
        if conversation_history and conversation_history[-1].role == "user":
            return f"Simulated AI: Understood your point about '{conversation_history[-1].content}'. How can I help refine the style for campaign {campaign_id} further?"
        return "Simulated AI: Hello! How can I assist with your email campaign style today?"

    # client = OpenAI(api_key=current_api_key) # Uncomment when using actual API

    # Prepare messages for the LLM
    llm_messages = []
    has_system_prompt = any(msg.role == "system" for msg in conversation_history)

    if not has_system_prompt:
        user_display_name = current_user.full_name if current_user.full_name else "the sender"

        system_prompt_content = (
            f"You are an AI assistant helping a user define the style, tone, and key messages "
            f"for an email campaign (ID: {campaign_id}). The email will be sent by {user_display_name}. "
            f"Guide the user to refine their email strategy. Ask clarifying questions if needed. "
            f"When the user seems satisfied, you can suggest they finalize the style."
        )
        llm_messages.append({"role": "system", "content": system_prompt_content})

    for msg in conversation_history:
        llm_messages.append({"role": msg.role, "content": msg.content})

    print("\n--- Attempting LLM Chat API Call (Commented Out) ---")
    # print(f"Formatted messages for LLM: {json.dumps(llm_messages, indent=2)}") # For debugging
    print(f"Conversation history has {len(llm_messages)} messages. Last user message: '{conversation_history[-1].content if conversation_history and conversation_history[-1].role == 'user' else 'N/A'}'")
    print("--------------------------------------------------\n")

    ai_reply_content = ""
    # === Example of actual LLM API call (Commented Out) ===
    # try:
    #     response = client.chat.completions.create(
    #         model="gpt-3.5-turbo",  # Or your preferred model
    #         messages=llm_messages,
    #         temperature=0.7,
    #         max_tokens=300
    #     )
    #     ai_reply_content = response.choices[0].message.content.strip()
    #     if not ai_reply_content:
    #         raise LLMIntegrationError("LLM returned an empty chat response.")
    # except Exception as e:
    #     print(f"LLM API call error: {e}")
    #     ai_reply_content = "Simulated AI: There was an issue processing your request. Let's try again." # Fallback
    # =======================================================

    if not ai_reply_content: # This will be true if the above block is commented out
        print("Using simulated LLM chat response as the API call block is commented out.")
        if conversation_history and conversation_history[-1].role == "user":
            user_last_message = conversation_history[-1].content.lower()
            if "hello" in user_last_message or "hi" in user_last_message:
                ai_reply_content = f"Simulated AI: Hello there! How can we shape the email for campaign {campaign_id} today?"
            elif "tone" in user_last_message:
                ai_reply_content = f"Simulated AI: Let's discuss the tone for campaign {campaign_id}. What are you aiming for? Professional, friendly, urgent?"
            elif "style" in user_last_message:
                ai_reply_content = f"Simulated AI: Regarding style for campaign {campaign_id}, what elements are you considering? Short sentences, emojis, specific CTAs?"
            else:
                ai_reply_content = f"Simulated AI: Thanks for your input on '{conversation_history[-1].content}'. What's the next step for campaign {campaign_id}?"
        else:
            ai_reply_content = f"Simulated AI: Please provide your first instruction for campaign {campaign_id}."

    return ai_reply_content


async def example_llm_usage():
    """Example of how generate_personalized_email might be called."""
    # Mock User ORM object
    # For example_llm_usage, if UserORMModel is used, it won't have user_role or user_company_name directly
    # This example might need adjustment if it's to be run directly with UserORMModel
    sample_user = UserORMModel( # Assuming UserORMModel can be instantiated like this for example
        id=1, # Dummy ID
        email="user@example.com", # Dummy email
        full_name="Manthan Example",
        is_active=True,
        is_superuser=False
        # Note: user_role and user_company_name are not direct fields of UserORMModel
    )
    # To make the example work as before for generate_personalized_email, we'd need to handle this differently
    # For now, the focus is generate_chat_response.
    # If generate_personalized_email is called with UserORMModel, it might error or behave differently
    # as current_user.user_role and current_user.user_company_name might be missing.
    # This part of the example is left as is, acknowledging this discrepancy for now.
    # It will effectively use None for those fields if UserORMModel doesn't have them.
    # To properly test generate_personalized_email, one might need to mock these attributes if they're expected.
    # For this subtask, we ensure generate_chat_response is correct.

    sample_user_prompt = "Introduce our new SuperWidget product. It's revolutionary and saves 50% time."
    sample_contact = {
        "first_name": "Alice",
        "last_name": "Wonderland",
        "email": "alice@example.com",
        "job_title": "Chief Innovation Officer",
        "company_name": "Wonderland Innovations",
        "industry": "Creative Solutions"
    }

    print(f"--- Running LLM Email Generation Example for {sample_contact['email']} ---")
    try:
        subject, body = await generate_personalized_email(
            user_core_prompt=sample_user_prompt,
            contact_data=sample_contact,
            current_user=sample_user # This will pass UserORMModel to generate_personalized_email
            # api_key="YOUR_OPENAI_KEY" # Optionally pass key here
        )
        print(f"\nGenerated Subject: {subject}")
        print(f"\nGenerated Body:\n{body}")
    except LLMIntegrationError as e:
        print(f"Error generating email: {e}")
    except Exception as e:
        print(f"An unexpected error in example usage: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(example_llm_usage())