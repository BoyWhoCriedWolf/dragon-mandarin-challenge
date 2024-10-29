"""
Uses the new structured outputs feature from OpenAI.
"""

import textwrap
from django.conf import settings
from openai import OpenAI

# This is the latest that supports Structured Outputs at the time of writing
DEFAULT_MODEL = "gpt-4o-2024-08-06"

client = OpenAI(api_key=settings.OPENAI_API_KEY)

def get_response_structured(prompt, structure, model=DEFAULT_MODEL, temperature=None, show_prompt=False):

    if isinstance(prompt, list):
        messages = prompt
    else:
        prompt = textwrap.dedent(prompt)
        messages = [
            # {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ]

    args = {
        "model": model,
        "messages": messages,
        'response_format': structure,
    }
    if temperature is not None:
        args['temperature'] = temperature

    if show_prompt:
        print(prompt)

    try:
        completion = client.beta.chat.completions.parse(**args)
        return completion.choices[0].message.parsed
    except:
        print("OpenAI request failed")
        raise




