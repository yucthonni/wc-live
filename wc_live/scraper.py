"""zhibo8 文字直播数据采集模块"""

import re
import json
import time
import random
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field

import requests
from bs4 import BeautifulSoup

# 请求头
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


# ---------- 数据结构 ----------

@dataclass
class MatchInfo:
    """一场比赛的摘要信息"""
    home_team: str
    away_team: str
    match_time: str          # 如 "01:00"
    match_date: str          # 如 "2026-06-18"
    saishi_id: str           # 直播吧比赛ID（也是API key）
    league: str = ""         # 联赛名称
    home_score: str = ""     # 当前比分
    away_score: str = ""


@dataclass
class LiveTextEntry:
    """一条文字直播记录"""
    live_id: str
    live_sid: str
    user_chn: str            # 作者（如"蝎子"）
    live_text: str           # 文字内容
    live_time: str           # 时间戳
    home_score: str = ""     # 主队比分
    visit_score: str = ""    # 客队比分
    pid_text: str = ""       # 状态（未赛/进行中/已结束）
    event: str = ""          # 事件图标（进球/红牌等）
    text_color: str = ""     # 文字颜色
    text_url: str = ""       # 关联新闻链接
    img_url: str = ""        # 图片链接
    text_bold: bool = False  # 是否加粗
    live_ptime: str = ""     # 比赛时间（如 57'24''）


# ---------- 匹配列表采集 ----------

def fetch_today_matches() -> list[MatchInfo]:
    """从直播吧首页获取今天的比赛列表"""
    url = "https://www.zhibo8.com/"
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.encoding = "utf-8"
    soup = BeautifulSoup(resp.text, "lxml")

    matches = []

    # 找赛程列表区域
    schedule_box = soup.select_one(".schedule_list, .list-item-box, .schedule")
    if not schedule_box:
        # 备用：直接找所有带 saishi_id 的链接
        for tag in soup.find_all("a", href=re.compile(r"match(\d+)v\.htm")):
            m = re.search(r"match(\d+)v\.htm", tag.get("href", ""))
            if m:
                saishi_id = m.group(1)
                parent_text = tag.parent.get_text(" ", strip=True) if tag.parent else ""
                matches.append(MatchInfo(
                    home_team=parent_text,
                    away_team="",
                    match_time="",
                    match_date="",
                    saishi_id=saishi_id,
                ))
        return matches

    # 按日期分组的列表处理
    # 需要更精细的解析
    return matches


def fetch_all_matches() -> list[MatchInfo]:
    """获取首页可见的所有比赛（含未来几日）"""
    url = "https://www.zhibo8.com/"
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.encoding = "utf-8"
    html = resp.text

    matches = []
    current_date = ""
    lines = html.split("\n")

    for i, line in enumerate(lines):
        line_s = line.strip()
        # 识别日期行
        date_m = re.search(r"(\d+)月(\d+)日", line_s)
        if date_m:
            month, day = date_m.groups()
            current_date = f"2026-{int(month):02d}-{int(day):02d}"
            continue

        # 识别比赛行
        match_m = re.search(
            r'(\d+:\d+).*?([\u4e00-\u9fff][\u4e00-\u9fff\s]*)'
            r'\s*(-|\d+:\d+)\s*'
            r'([\u4e00-\u9fff][\u4e00-\u9fff\s]*)',
            line_s,
        )
        # 找 saishi_id
        saishi_m = re.search(r"match(\d+)v\.htm", line_s)

        if saishi_m:
            saishi_id = saishi_m.group(1)
            match_time = ""
            home_team = ""
            away_team = ""
            score = ""

            # 尝试从上下文中解析更多信息
            context = line_s
            time_m = re.search(r"(\d+:\d+)", context)
            if time_m:
                match_time = time_m.group(1)

            # 解析队名和比分（简单模式）
            parts = re.split(r"\s{2,}|\|", context)
            for p in parts:
                p = p.strip()
                if re.match(r"\d+:\d+", p) and not p.startswith("http"):
                    score = p
                elif re.match(r"[\u4e00-\u9fff}]", p) and ":" not in p and len(p) > 1:
                    if not home_team:
                        home_team = p
                    elif not away_team:
                        away_team = p

            matches.append(MatchInfo(
                home_team=home_team,
                away_team=away_team,
                match_time=match_time,
                match_date=current_date,
                saishi_id=saishi_id,
                league="世界杯" if "世界杯" in context else "",
            ))

    return matches


def fetch_match_page(saishi_id: str) -> dict:
    """解析比赛页面，获取页面中的 p_* 变量"""
    url = f"https://www.zhibo8.com/zhibo/zuqiu/2026/match{saishi_id}v.htm"
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.encoding = "utf-8"
    html = resp.text

    data = {}
    # 提取 inline 变量
    patterns = {
        "home_team": r"var\s+p_host\s*=\s*['\"]([^'\"]+)['\"]",
        "away_team": r"var\s+p_guest\s*=\s*['\"]([^'\"]+)['\"]",
        "match_date": r"var\s+p_game_date\s*=\s*['\"]([^'\"]+)['\"]",
        "match_time": r"var\s+p_match_time\s*=\s*['\"]([^'\"]+)['\"]",
        "saishi_id": r"var\s+p_saishi_id\s*=\s*['\"]([^'\"]+)['\"]",
        "league_type": r"var\s+p_type\s*=\s*['\"]([^'\"]+)['\"]",
    }
    for key, pat in patterns.items():
        m = re.search(pat, html)
        if m:
            data[key] = m.group(1)

    return data


# ---------- 文字直播API ----------

# 可能的服务器前缀
_SERVERS = ["dingshi4pc", "dingshi145", "dingshia", "dingshib",
            "dingshic", "dingshid", "dingshie"]


def _find_server(saishi_id: str) -> Optional[str]:
    """尝试找到可用的服务器"""
    for sv in _SERVERS:
        url = (
            f"https://{sv}.qiumibao.com/livetext/data/cache/"
            f"livetext/{saishi_id}/0/max_sid.json"
        )
        try:
            resp = requests.get(url, headers=HEADERS, timeout=5)
            if resp.status_code == 200:
                return sv
        except requests.RequestException:
            continue
    return None


def get_max_sid(saishi_id: str, server: str = "dingshi4pc") -> int:
    """获取当前最大 live_sid"""
    url = (
        f"https://{server}.qiumibao.com/livetext/data/cache/"
        f"livetext/{saishi_id}/0/max_sid.json"
    )
    resp = requests.get(url, headers=HEADERS, timeout=10)
    data = resp.json()
    return int(data.get("max_sid", 0))


def get_live_texts(saishi_id: str, sid: int, server: str = "dingshi4pc") -> list[LiveTextEntry]:
    """获取指定 live_sid 的文字直播数据。

    live_sid 对应 URL 中的 id，规则：
    - ID 从 0 开始，步进为 2，使用 URL id = sid 向上取整到偶数
    """
    # sid 到 URL id 的映射：URL id = int(sid / 2) * 2
    url_id = int(sid / 2) * 2

    url = (
        f"https://{server}.qiumibao.com/livetext/data/cache/"
        f"livetext/{saishi_id}/0/lit_page_2/{url_id}.htm"
    )
    resp = requests.get(url, headers=HEADERS, timeout=10)
    if resp.status_code != 200:
        return []

    try:
        raw = resp.json()
    except json.JSONDecodeError:
        return []

    entries = []
    for item in raw:
        entries.append(LiveTextEntry(
            live_id=item.get("live_id", ""),
            live_sid=item.get("live_sid", "0"),
            user_chn=item.get("user_chn", ""),
            live_text=item.get("live_text", ""),
            live_time=item.get("live_time", ""),
            home_score=item.get("home_score", ""),
            visit_score=item.get("visit_score", ""),
            pid_text=item.get("pid_text", ""),
            event=item.get("event", ""),
            text_color=item.get("text_color", ""),
            text_url=item.get("text_url", ""),
            img_url=item.get("img_url", ""),
            text_bold=item.get("text_bold", False),
            live_ptime=item.get("live_ptime", ""),
        ))
    return entries


def is_match_ongoing(saishi_id: str, server: str = "dingshi4pc") -> Optional[bool]:
    """检查比赛是否进行中"""
    entries = get_live_texts(saishi_id, 0, server)
    for e in entries:
        if e.pid_text:
            if "未赛" in e.pid_text:
                return False
            if "结束" in e.pid_text or "完赛" in e.pid_text:
                return False
            if "进行" in e.pid_text or "中" in e.pid_text:
                return True
    return None


def poll_live_text(saishi_id: str, server: str = "dingshi4pc",
                   interval: float = 5.0, callback=None):
    """轮询文字直播更新。

    Args:
        saishi_id: 比赛ID
        server: API服务器
        interval: 轮询间隔（秒）
        callback: 回调函数，参数为 (list[LiveTextEntry], is_new)
    """
    last_sid = get_max_sid(saishi_id, server)

    while True:
        try:
            current_max = get_max_sid(saishi_id, server)
        except Exception:
            time.sleep(interval)
            continue

        if current_max > last_sid:
            # 有新的文字直播
            new_entries = []
            for sid in range(last_sid + 1, current_max + 1):
                entries = get_live_texts(saishi_id, sid, server)
                new_entries.extend(entries)
                time.sleep(random.uniform(0.3, 0.8))  # 反爬延迟

            if new_entries:
                new_entries.sort(key=lambda e: e.live_sid)
                if callback:
                    callback(new_entries, is_new=True)
            last_sid = current_max

        time.sleep(interval + random.uniform(0, 1))


# ---------- 辅助 ----------

def get_match_status(saishi_id: str, server: str = "dingshi4pc") -> dict:
    """检测比赛状态"""
    status = {
        "status": "unknown",
        "status_text": "未知",
        "score": "",
        "period": "",
    }
    
    # 获取最新数据
    max_sid = get_max_sid(saishi_id, server)
    if max_sid == 0:
        status["status"] = "not_started"
        status["status_text"] = "⏳ 未开赛"
        return status
    
    entries = get_live_texts(saishi_id, max_sid, server)
    if not entries:
        status["status"] = "not_started"
        status["status_text"] = "⏳ 未开赛"
        return status
    
    latest = entries[-1]
    
    # 检查 pid_text 字段
    pid_text = latest.pid_text.lower() if latest.pid_text else ""
    
    if "中场" in pid_text or "半场" in pid_text:
        status["status"] = "halftime"
        status["status_text"] = "⏸️ 中场休息"
    elif "结束" in pid_text or "完赛" in pid_text or "终场" in pid_text:
        status["status"] = "finished"
        status["status_text"] = "🏁 已结束"
    elif "未赛" in pid_text or "赛前" in pid_text:
        status["status"] = "not_started"
        status["status_text"] = "⏳ 未开赛"
    elif "进行" in pid_text or "上半" in pid_text or "下半" in pid_text:
        status["status"] = "live"
        status["status_text"] = "🔴 进行中"
    else:
        # 根据时间判断
        status["status"] = "live"
        status["status_text"] = "🔴 进行中"
    
    # 比分
    if latest.home_score or latest.visit_score:
        status["score"] = f"{latest.home_score or '0'} - {latest.visit_score or '0'}"
    
    # 半场信息
    if "上半" in pid_text:
        status["period"] = "上半场"
    elif "下半" in pid_text:
        status["period"] = "下半场"
    elif "加时" in pid_text:
        status["period"] = "加时赛"
    elif "点球" in pid_text:
        status["period"] = "点球大战"
    
    return status


def get_current_matches() -> list[MatchInfo]:
    """获取当前正在进行的世界杯比赛"""
    url = "https://www.zhibo8.com/"
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.encoding = "utf-8"

    # 提取所有足球比赛链接
    matches = []
    for m in re.finditer(
        r'href="([^"]*match(\d+)v\.htm)"[^>]*>'
        r'\s*([^<]*?)\s*</a>\s*([^<]*?)\s*</li>',
        resp.text,
    ):
        saishi_id = m.group(2)
        matches.append(MatchInfo(
            home_team="",
            away_team="",
            match_time="",
            match_date="",
            saishi_id=saishi_id,
        ))

    return matches
