"""终端显示模块 — 使用 rich 渲染文字直播"""

from datetime import datetime
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.columns import Columns
from rich import box

from .scraper import MatchInfo, LiveTextEntry


# 全局console
console = Console()

# 事件图标映射
EVENT_ICONS = {
    "live_ic_goal": "⚽",
    "live_ic_goal3x": "⚽",
    "live_ic_red_card": "🟥",
    "live_ic_yellow_card": "🟨",
    "live_ic_substitution": "🔄",
    "live_ic_penalty": "⚽",     # 点球
    "live_ic_own_goal": "⚽",    # 乌龙
    "live_ic_var": "📺",         # VAR
    "live_ic_news3x": "📰",     # 新闻/前瞻
    "live_ic_shot": "🔫",
    "live_ic_save": "🧤",
    "live_ic_corner": "🚩",
    "live_ic_foul": "🟡",
    "live_ic_offside": "🚩",
    "live_ic_injury": "🩹",
    "live_ic_half": "⏸️",
    "live_ic_fulltime": "🛑",
    "live_ic_start": "▶️",
}


def get_event_icon(event_name: str) -> str:
    """获取事件图标"""
    if not event_name:
        return ""
    # 尝试精确匹配
    if event_name in EVENT_ICONS:
        return EVENT_ICONS[event_name]
    # 模糊匹配
    for key, icon in EVENT_ICONS.items():
        if key in event_name:
            return icon
    return "•"


def format_live_text(entry: LiveTextEntry, use_icons: bool = True) -> Text:
    """将一条文字直播记录格式化为 rich Text"""
    parts = []

    # 时间
    # 优先用比赛时间，否则用wall time
    time_str = ""
    if entry.live_ptime:
        time_str = entry.live_ptime
    elif entry.live_time:
        try:
            dt = datetime.strptime(entry.live_time, "%Y-%m-%d %H:%M:%S")
            time_str = dt.strftime("%H:%M")
        except ValueError:
            time_str = entry.live_time[-8:-3] if len(entry.live_time) >= 8 else entry.live_time

    # 状态标签
    pid_prefix = ""
    if entry.pid_text:
        if "未赛" in entry.pid_text:
            pid_prefix = "[未赛]"
        elif "结束" in entry.pid_text or "完赛" in entry.pid_text:
            pid_prefix = "[完赛]"

    if time_str:
        parts.append(Text(f"[{time_str}]", style="dim white"))

    # 事件图标
    if use_icons and entry.event:
        icon = get_event_icon(entry.event)
        if icon:
            parts.append(Text(f" {icon} ", style="bold"))

    # 比分变化
    score_str = ""
    if entry.home_score or entry.visit_score:
        score_str = f" {entry.home_score or '?'} - {entry.visit_score or '?'} "
        parts.append(Text(score_str, style="bold yellow"))

    # 作者
    if entry.user_chn and "系統" not in entry.user_chn:
        parts.append(Text(f" {entry.user_chn}: ", style="dim cyan"))

    # 文字内容
    text_content = entry.live_text.strip()
    if entry.text_bold:
        parts.append(Text(text_content, style="bold white"))
    else:
        parts.append(Text(text_content, style="white"))

    # 如果有关联图片
    if entry.img_url:
        parts.append(Text(" 📷", style="dim"))

    result = Text.assemble(*parts)

    # 文字颜色
    if entry.text_color:
        result.stylize(entry.text_color)

    return result


def render_match_header(match: MatchInfo) -> Panel:
    """渲染比赛头部信息"""
    now = datetime.now().strftime("%H:%M:%S")

    text = Text()
    text.append(f"{match.home_team}", style="bold cyan")
    text.append(" vs ", style="yellow bold")
    text.append(f"{match.away_team}", style="bold magenta")

    if match.home_score or match.away_score:
        text.append(f"\n当前比分: ", style="white")
        text.append(f"{match.home_score or '0'} - {match.away_score or '0'}", style="bold yellow")

    text.append(f"\n{match.league}", style="dim")
    text.append(f" | {match.match_date} {match.match_time}", style="dim")

    return Panel(
        text,
        title=f"🎯 [bold]文字直播[/bold]",
        subtitle=f"更新于 {now}",
        border_style="green",
        box=box.DOUBLE,
    )


def render_live_list(entries: list[LiveTextEntry], max_entries: int = 50) -> list[Text]:
    """渲染文字直播列表（最新在前面）"""
    sorted_entries = sorted(entries, key=lambda e: e.live_time, reverse=True)
    if len(sorted_entries) > max_entries:
        # 显示一条提示
        result = [Text(f"[dim]... 共 {len(sorted_entries)} 条，显示最近 {max_entries} 条 ...[/dim]")]
        sorted_entries = sorted_entries[:max_entries]
    else:
        result = []

    for entry in reversed(sorted_entries):  # 最早的在前
        result.append(format_live_text(entry))

    return result


def render_help_panel() -> Panel:
    """渲染帮助面板"""
    return Panel(
        Text.assemble(
            ("q / Ctrl+C ", "bold yellow"), ("退出\n", "white"),
            ("r ", "bold yellow"), ("手动刷新\n", "white"),
            ("d ", "bold yellow"), ("切换 Dark/Light 模式\n", "white"),
            ("? / h ", "bold yellow"), ("显示/隐藏帮助", "white"),
        ),
        title="💡 快捷键",
        border_style="blue",
        box=box.SQUARE,
    )


def render_matches_table(matches: list[MatchInfo]) -> Table:
    """渲染比赛列表表格"""
    table = Table(
        title="🎯 直播吧 - 世界杯比赛",
        box=box.ROUNDED,
        border_style="green",
        header_style="bold white",
    )

    table.add_column("#", style="dim", width=3)
    table.add_column("时间", style="cyan", width=8)
    table.add_column("联赛", style="dim", width=12)
    table.add_column("主队", style="bold", width=20)
    table.add_column("比分", style="yellow", width=8, justify="center")
    table.add_column("客队", style="bold", width=20)

    for i, m in enumerate(matches, 1):
        home = m.home_team
        away = m.away_team
        score = f"{m.home_score or '?'} - {m.away_score or '?'}"
        league = m.league or "世界杯"

        table.add_row(
            str(i),
            m.match_time,
            league,
            home,
            score,
            away,
        )

    return table
