import httpx

from app.config import Settings

settings = Settings()


async def call_llm(config, prompt: str) -> str:
    headers = {
        'Authorization': f'Bearer {config.api_key}',
        'Content-Type': 'application/json',
    }
    payload = {
        'model': config.model,
        'messages': [{'role': 'user', 'content': prompt}],
        'temperature': 0.3,
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(f'{config.endpoint}/chat/completions', json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        return data['choices'][0]['message']['content']
