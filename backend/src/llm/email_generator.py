# backend/src/llm/email_generator.py
import os
import json # For potential structured output from LLM
from typing import Dict, Tuple, Optional

# Placeholder for actual LLM client library (e.g., from openai import OpenAI)
# For this subtask, we'll simulate the interaction.

# It's crucial to load API keys from environment variables or a secure config system.
# NEVER hardcode API keys.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# from openai import OpenAI # Ensure this import is uncommented when using actual API

# Assuming User ORM model is importable for type hinting
try:
    from src.models.user_models import User as UserORM
except ImportError:
    # Placeholder for User ORM model if actual import fails
    class UserORM: # type: ignore
        full_name: Optional[str] = "Sender Name"
        user_role: Optional[str] = "Team Member"
        user_company_name: Optional[str] = "Our Company"


class LLMIntegrationError(Exception):
    """Custom exception for LLM integration issues."""
    pass

def _construct_llm_prompt(
    user_core_prompt: str,
    contact_data: Dict[str, str],
    current_user: UserORM
) -> str:
    """
    Constructs a detailed prompt for the LLM to generate a personalized email,
    incorporating sender's details from the current_user object.
    """
    user_full_name = current_user.full_name or "a team member"
    user_company_name = current_user.user_company_name or "our company"
    user_role = current_user.user_role

    sender_intro = f"The email is from {user_full_name}"
    if user_role:
        sender_intro += f", {user_role}"
    sender_intro += f" at {user_company_name}."

    system_message = (
        "You are an expert marketing assistant. Your task is to write a professional, concise, and engaging "
        "outreach email. The email should be personalized for the recipient using the provided contact data. "
        "Generate a suitable subject line and the email body. Ensure the tone is appropriate for a first contact. "
        "Do not use placeholders like {{first_name}} in the final email; instead, use the actual values provided from the contact data. "
        f"{sender_intro}" # Incorporate sender's details
    )

    contact_context = "### Contact Data for Personalization:\n"
    for key, value in contact_data.items():
        contact_context += f"- {key.replace('_', ' ').title()}: {value}\n"

    full_prompt = f"""
{system_message}

### User's Core Request:
{user_core_prompt}

{contact_context}

### Your Task:
Based on the user's request and the contact data, generate:
1. A compelling subject line (label it as 'Subject:').
2. The full email body (label it as 'Body:').

Example of how to use contact data: If contact_data has 'first_name: John', use 'John' in the email, not '{{first_name}}'.
"""
    # No .format() needed for sender details as they are directly embedded in system_message
    return full_prompt


async def generate_personalized_email(
    user_core_prompt: str,
    contact_data: Dict[str, str], # e.g., {"first_name": "John", "company_name": "Acme Corp", ...}
    current_user: UserORM, # Pass the full User ORM object
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
        return _simulate_llm_response(user_core_prompt, contact_data, current_user)

    # client = OpenAI(api_key=current_api_key) # Uncomment when using actual API

    prompt_to_llm = _construct_llm_prompt(user_core_prompt, contact_data, current_user)

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
        return _simulate_llm_response(user_core_prompt, contact_data, current_user)

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


def _simulate_llm_response(user_core_prompt: str, contact_data: Dict[str, str], current_user: UserORM) -> Tuple[str, str]:
    """Provides a simulated LLM response for testing without making an actual API call."""
    user_full_name = current_user.full_name or "[Your Name/Signature]"
    user_company_name = current_user.user_company_name or "Our Company"

    print(f"Simulating LLM response for contact: {contact_data.get('email', 'N/A')}, from user: {user_full_name} at {user_company_name}")

    subject = f"Regarding {user_core_prompt[:20]}... for {contact_data.get('company_name', 'your company')}"
    body = f"""Hi {contact_data.get('first_name', 'Valued Professional')},

I hope this email finds you well.

I'm {user_full_name}, writing to you from {user_company_name}. We noticed your work at {contact_data.get('company_name', 'your company')} and were particularly interested in your role as {contact_data.get('job_title', 'a key player in your industry')}.

My core message is about: "{user_core_prompt}". We believe our solutions in this area could be highly beneficial for you.

Would you be available for a brief 15-minute chat next week to discuss how {user_company_name} can specifically help {contact_data.get('company_name', 'your team')}?

Best regards,
{user_full_name}
{current_user.user_role + ", " if current_user.user_role else ""}{user_company_name}
"""
    return subject, body


async def example_llm_usage():
    """Example of how generate_personalized_email might be called."""
    # Mock User ORM object
    sample_user = UserORM()
    sample_user.full_name = "Manthan"
    sample_user.user_role = "Founder"
    sample_user.user_company_name = "23Ventures"


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
            current_user=sample_user
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