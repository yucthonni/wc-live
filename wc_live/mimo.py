"""MiMo API 集成 — AI 解说与赛事总结"""

import os
import json
from typing import Optional

import requests


# MiMo API 配置
MIMO_BASE = "https://api.xiaomimimo.com/v1"
MIMO_MODEL = "mimo-v2.5"


def get_mimo_api_key() -> Optional[str]:
    """从环境变量或 Hermes 配置中获取 MiMo API Key"""
    key = os.environ.get("MIMO_API_KEY")
    if key:
        return key
    # 尝试从 Hermes 配置读取
    config_path = os.path.expanduser("~/.hermes/config.yaml")
    if os.path.exists(config_path):
        with open(config_path) as f:
            for line in f:
                if "mimo" in line.lower() and "api" in line.lower() and "key" in line.lower():
                    if ":" in line:
                        return line.split(":", 1)[1].strip().strip('"').strip("'")
    return None


def _call_mimo(messages: list[dict], api_key: str,
               model: str = MIMO_MODEL) -> Optional[str]:
    """调用 MiMo API"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 2000,
    }

    try:
        resp = requests.post(
            f"{MIMO_BASE}/chat/completions",
            headers=headers,
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"[MiMo API 调用失败: {e}]"


def summarize_match(entries_text: str, home_team: str = "",
                    away_team: str = "") -> Optional[str]:
    """用 MiMo 总结比赛关键事件"""
    api_key = get_mimo_api_key()
    if not api_key:
        return None

    prompt = f"""你是一个体育解说员。请根据下面的文字直播记录，用中文总结这场比赛的关键事件。

{'主队: ' + home_team if home_team else ''}
{'客队: ' + away_team if away_team else ''}

文字直播记录:
{entries_text}

请按时间顺序列出关键事件（进球、红黄牌、换人、争议判罚等），每行一条，保持简洁。如果已有比分变化，请标注。
"""

    messages = [
        {"role": "system", "content": "你是专业体育解说员，擅长从文字直播中提炼比赛精华。"},
        {"role": "user", "content": prompt},
    ]

    return _call_mimo(messages, api_key)


def chat_about_match(user_input: str, match_context: str) -> Optional[str]:
    """与用户讨论比赛情况"""
    api_key = get_mimo_api_key()
    if not api_key:
        return None

    messages = [
        {
            "role": "system",
            "content": "你是直播吧的文字直播助理。用中文回答用户关于比赛的问题。"
                       "保持简洁、准确、有趣。不要虚构没有的信息。",
        },
        {"role": "user", "content": f"比赛背景:\n{match_context}\n\n用户: {user_input}"},
    ]

    return _call_mimo(messages, api_key)
