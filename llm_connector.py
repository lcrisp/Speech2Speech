# llm_connector.py (memory now stores user+assistant pairs)

import requests
from load_conf import (
    LLM_SYSTEM_PROMPT,
    LLM_IDENTITY,
    LLM_SCENE,
    LLM_API_URL,
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS,
    LLM_STOP,
    MEMORY_ENABLED,
    MEMORY_CHAR_LIMIT,
    LLM_CHAT_MODE,
)

scene_used = False  # scene injected once per session
memory_buffer = []  # stores (user, assistant) tuples


def build_system_prompt():
    global scene_used
    parts = [LLM_SYSTEM_PROMPT.strip()]
    if LLM_IDENTITY:
        parts.append(LLM_IDENTITY.strip())
    if LLM_SCENE and not scene_used:
        parts.append(LLM_SCENE.strip())
        scene_used = True
    return "\n\n".join(parts)


def update_memory(user, reply):
    global memory_buffer
    if not MEMORY_ENABLED:
        return
    memory_buffer.append((user.strip(), reply.strip()))
    # trim buffer based on combined char length
    while sum(len(u) + len(r) for u, r in memory_buffer) > MEMORY_CHAR_LIMIT:
        memory_buffer.pop(0)


def get_memory_snippet():
    if not MEMORY_ENABLED or not memory_buffer:
        return ""
    return "\n\n".join([f"User: {u}\nAssistant: {r}" for u, r in memory_buffer[-3:]])


class LLMConnector:
    def __init__(self):
        self.url = LLM_API_URL

    def query(self, user_text: str):
        system_prompt = build_system_prompt()
        memory_context = get_memory_snippet()

        full_user_input = user_text.strip()
        if memory_context:
            full_user_input = f"{memory_context}\n\n{user_text.strip()}"

        if LLM_CHAT_MODE:
            payload = {
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": full_user_input},
                ],
                "temperature": LLM_TEMPERATURE,
                "max_tokens": LLM_MAX_TOKENS,
                "stop": LLM_STOP,
            }
        else:
            prompt = f"{system_prompt}\n\nUser: {full_user_input}\n\nAssistant:"
            payload = {
                "prompt": prompt,
                "temperature": LLM_TEMPERATURE,
                "max_tokens": LLM_MAX_TOKENS,
                "stop": LLM_STOP,
            }

        print("[LLMConnector] Sending request to LM Studio...")
        print("[LLMConnector] Payload being sent:")
        import json
        print(json.dumps(payload, indent=2))

        response = requests.post(self.url, json=payload)
        response.raise_for_status()
        data = response.json()

        if LLM_CHAT_MODE:
            reply = data["choices"][0]["message"]["content"]
        else:
            reply = data["text"]

        update_memory(user_text, reply)
        return reply
