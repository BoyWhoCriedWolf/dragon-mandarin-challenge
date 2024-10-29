import asyncio
import random
import textwrap
import time
import traceback
import json5
from django.conf import settings

import openai as openai
from openai import RateLimitError


DEFAULT_MODEL = "gpt-3.5-turbo"

N_ATTEMPTS = 5

client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
client_async = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

class GPTError(Exception):
    pass

def _process_response(response, json_keys):
    res_text = response.choices[0].message.content
    print(f"Raw GPT response: {res_text}")

    if json_keys:

        try:
            start_index = res_text.find('{')
            end_index = res_text.rfind('}') + 1
            if start_index != -1 and end_index != -1:
                # json5 is a bit more liberal (e.g. GPT likes to add trailing commas), so use that
                json_data = json5.loads(res_text[start_index:end_index])
                if all(key in json_data for key in json_keys):
                    return json_data
                else:
                    print("JSON is well formed, but missing required key")
            else:
                print("Could not find start { or end }")

        except ValueError:
            # json5 seems to raise ValueError rather than JSONDecodeError on invalid JSON
            traceback.print_exc()
            pass

        print(f"Response did not contain the required JSON: {res_text}")
        return None

    else:
        return res_text


async def get_conversation_response_async(messages, json_keys=None, model=DEFAULT_MODEL):

    print(messages)
    print(f"Model: {model}")

    for attempt in range(N_ATTEMPTS):
        print(f"Calling GPT (attempt {attempt + 1})")
        try:
            response = await client_async.chat.completions.create(
                model=model,
                messages=messages,
            )
        except RateLimitError:
            for h in response.headers:
                print(h)
            print("Rate limited - retrying in about 1 second")
            await asyncio.sleep(random.uniform(0.5, 1.5))
            continue

        except Exception as e:
            print(f"Error getting response from OpenAI, retrying. Error: {type(e).__name__}, Message: {str(e)}")
            continue

        res = _process_response(response, json_keys)
        if res is not None:
            return res

    raise GPTError(f"GPT failed after {N_ATTEMPTS} attempts")


def get_conversation_response(messages, json_keys=None, model=DEFAULT_MODEL):
    print(messages)
    print(f"Model: {model}")

    for attempt in range(N_ATTEMPTS):
        print(f"Calling GPT (attempt {attempt + 1})")
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
            )
        except RateLimitError:
            for h in response.headers:
                print(h)
            print("Rate limited - retrying in about 1 second")
            time.sleep(random.uniform(0.5, 1.5))
            continue

        except Exception as e:
            print(f"Error getting response from OpenAI, retrying. Error: {type(e).__name__}, Message: {str(e)}")
            continue

        res = _process_response(response, json_keys)
        if res is not None:
            return res

    raise GPTError(f"GPT failed after {N_ATTEMPTS} attempts")


async def get_response_async(prompt, json_keys=None, model=DEFAULT_MODEL):

    prompt = textwrap.dedent(prompt).strip()
    messages = [
        {"role": "system", "content": "You are a helpful language assistant."},
        {"role": "user", "content": prompt},
    ]
    return await get_conversation_response_async(messages, json_keys, model=model)


def get_response(prompt, json_keys=None, model=DEFAULT_MODEL):

    prompt = textwrap.dedent(prompt).strip()
    messages = [
        {"role": "system", "content": "You are a helpful language assistant."},
        {"role": "user", "content": prompt},
    ]
    return get_conversation_response(messages, json_keys, model=model)










