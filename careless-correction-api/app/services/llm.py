import ipaddress
import socket
from urllib.parse import urlparse

import httpx

from app.config import Settings

settings = Settings()


def validate_endpoint(endpoint: str, allow_private: bool = False) -> str:
    """校验 LLM endpoint，阻止 SSRF（把地址指向内网/回环/云元数据服务）。

    只允许 http/https 且主机解析后不得落在私有/保留地址段。
    确实需要连内网自建模型时，设置 LLM_ALLOW_PRIVATE_ENDPOINT=true。
    """
    raw = (endpoint or '').strip()
    if not raw:
        raise ValueError('LLM endpoint 未配置')
    parsed = urlparse(raw)
    if parsed.scheme not in ('http', 'https'):
        raise ValueError('LLM endpoint 必须是 http:// 或 https:// 地址')
    host = parsed.hostname
    if not host:
        raise ValueError('LLM endpoint 缺少主机名')
    if allow_private:
        return raw.rstrip('/')

    port = parsed.port or (443 if parsed.scheme == 'https' else 80)
    try:
        infos = socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise ValueError(f'无法解析 LLM endpoint 域名：{host}') from exc

    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if (
            ip.is_private or ip.is_loopback or ip.is_link_local
            or ip.is_reserved or ip.is_multicast or ip.is_unspecified
        ):
            raise ValueError(
                'LLM endpoint 指向内网/保留地址，已拒绝；'
                '如需连接内网自建模型请设置 LLM_ALLOW_PRIVATE_ENDPOINT=true'
            )
    return raw.rstrip('/')


async def call_llm(config, prompt: str) -> str:
    base = validate_endpoint(config.endpoint, settings.llm_allow_private_endpoint)
    headers = {
        'Authorization': f'Bearer {config.api_key}',
        'Content-Type': 'application/json',
    }
    payload = {
        'model': config.model,
        'messages': [{'role': 'user', 'content': prompt}],
        'temperature': 0.3,
    }
    async with httpx.AsyncClient(timeout=30, follow_redirects=False) as client:
        resp = await client.post(f'{base}/chat/completions', json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        try:
            return data['choices'][0]['message']['content']
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError('LLM 返回内容格式不符合预期') from exc
