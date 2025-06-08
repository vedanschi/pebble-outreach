# backend/src/llm/email_generator.py
import os
import json # For potential structured output from LLM
from typing import Dict, Tuple, Optional

# Placeholder for actual LLM client library (e.g., from openai import OpenAI)
# For this subtask, we'll simulate the interaction.

# It's crucial to load API keys from environment variables or a secure config system.
# NEVER hardcode API keys.
# LLM_API_KEY = os.getenv("OPENAI_API_KEY") # Example for OpenAI

class LLMIntegrationError(Exception):
    """Custom exception for LLM integration issues."""
    pass

def _construct_llm_prompt(
    user_core_prompt: str,
    contact_data: Dict[str, str],
    your_company_name: str = "Our Company" # Default, should be configurable
) -> str:
    """
    Constructs a detailed prompt for the LLM to generate a personalized email.
    """

    # These are examples; actual placeholders should match contact_data keys
    # personalization_details = "\n".join(
    #     f"- {key.replace('_', ' ').title()}: {{{key}}}" for key in contact_data.keys()
    # ) # This line was for template-based generation, not direct use by LLM.

    # Example system message. This can be fine-tuned significantly.
    system_message = (
        "You are an expert marketing assistant. Your task is to write a professional, concise, and engaging "
        "outreach email. The email should be personalized for the recipient using the provided contact data. "
        "Generate a suitable subject line and the email body. Ensure the tone is appropriate for a first contact."
        "Do not use placeholders like {{first_name}} in the final email, instead, use the actual values provided."
        "The email is from {your_company_name}."
    )

    # Providing the contact data directly in the prompt for the LLM to use.
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
    # We need to format your_company_name into the system_message part of the prompt.
    # The **contact_data is not used by .format() here as data is already in contact_context.
    return full_prompt.format(your_company_name=your_company_name)


async def generate_personalized_email(
    user_core_prompt: str,
    contact_data: Dict[str, str], # e.g., {"first_name": "John", "company_name": "Acme Corp", ...}
    api_key: Optional[str] = None,
    your_company_name: str = "Our Company"
) -> Tuple[str, str]:
    """
    Generates a personalized email subject and body using an LLM.

    Args:
        user_core_prompt: The user's high-level instruction for the email.
        contact_data: A dictionary containing personalization data for the contact.
        api_key: The LLM API key. If None, it will try to use a pre-configured key (e.g., env var).
        your_company_name: The name of the company sending the email.

    Returns:
        A tuple (subject, body).

    Raises:
        LLMIntegrationError: If there's an issue with the LLM API call or response.
    """

    # In a real app, api_key would be fetched securely if not provided.
    # current_api_key = api_key or os.getenv("OPENAI_API_KEY")
    # if not current_api_key:
    #     raise LLMIntegrationError("LLM API key not provided or configured.")

    # client = OpenAI(api_key=current_api_key) # Example: Initialize OpenAI client

    prompt_to_llm = _construct_llm_prompt(user_core_prompt, contact_data, your_company_name)

    print("\n--- Sending to LLM (Simulation) ---")
    # print(prompt_to_llm) #  Can be very verbose
    print("Prompt constructed. Length:", len(prompt_to_llm))
    print("------------------------------------\n")

    # === Placeholder for actual LLM API call ===
    # try:
    #     response = client.chat.completions.create(
    #         model="gpt-3.5-turbo", # Or other preferred model
    #         messages=[
    #             # System message is now part of the main prompt_to_llm
    #             {"role": "user", "content": prompt_to_llm}
    #         ],
    #         temperature=0.7, # Adjust for creativity vs. predictability
    #         max_tokens=500  # Adjust as needed
    #     )
    #     generated_text = response.choices[0].message.content.strip()
    # except Exception as e:
    #     # Handle various API errors (rate limits, auth, network, etc.)
    #     raise LLMIntegrationError(f"LLM API call failed: {e}")
    # ==========================================

    # Simulate LLM response for this subtask
    # Using f-string for more dynamic simulation based on input
    simulated_llm_output = f"""
Subject: Personalized Intro to Our AI Solutions for {contact_data.get('company_name', 'Your Company')}
Body:
Hi {contact_data.get('first_name', 'Valued Professional')},

I hope this email finds you well.

I'm writing to you from {your_company_name} because I came across your work at {contact_data.get('company_name', 'your company')} and was impressed by your role as {contact_data.get('job_title', 'a key player in your industry')}.

We specialize in helping companies like yours leverage cutting-edge solutions. Based on your core request: "{user_core_prompt}", we believe our offerings align perfectly with your needs.

Would you be open to a brief 15-minute call next week to explore how we can help {contact_data.get('company_name', 'your team')} achieve its goals?

Best regards,
[Your Name/Signature]
{your_company_name}
"""
    generated_text = simulated_llm_output

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


async def example_llm_usage():
    """Example of how generate_personalized_email might be called."""
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
        # In a real app, API key would be handled more securely
        subject, body = await generate_personalized_email(
            sample_user_prompt,
            sample_contact,
            your_company_name="My Awesome Startup Inc."
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