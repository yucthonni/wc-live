#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# <swiftbar.hideAbout>false</swiftbar.hideAbout>
# <swiftbar.hideRunInTerminal>false</swiftbar.hideRunInTerminal>
# <swiftbar.hideLastUpdated>false</swiftbar.hideLastUpdated>
# <swiftbar.hideDisablePlugin>false</swiftbar.hideDisablePlugin>
# <swiftbar.hideSwiftBar>false</swiftbar.hideSwiftBar>
# <swiftbar.menuFontSize>12</swiftbar.menuFontSize>
# <swiftbar.refresh>10</swiftbar.refresh>

"""
wc-live SwiftBar 插件 — Mac 菜单栏文字直播

配置: wc-live menu set <序号|saishi_id>
"""

import json
import sys
import os

CONFIG_FILE = os.path.expanduser("~/.wc-live.json")
PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))
SCRAPER_DIR = os.path.dirname(PLUGIN_DIR)


def get_live_data(saishi_id: str):
    """获取最新文字直播数据"""
    try:
        import requests

        # 找可用服务器
        for sv in ["dingshi4pc", "dingshi145"]:
            try:
                url = f"https://{sv}.qiumibao.com/livetext/data/cache/livetext/{saishi_id}/0/max_sid.json"
                resp = requests.get(url, timeout=5)
                if resp.status_code == 200:
                    max_sid = resp.json().get("max_sid", 0)
                    if max_sid == 0:
                        return None, "未开赛"

                    url_id = int(max_sid / 2) * 2
                    api_url = f"https://{sv}.qiumibao.com/livetext/data/cache/livetext/{saishi_id}/0/lit_page_2/{url_id}.htm"
                    resp = requests.get(api_url, timeout=10)
                    data = resp.json()
                    if data:
                        return data[-1], None
                    return None, "无数据"
            except:
                continue

        return None, "无法连接服务器"
    except Exception as e:
        return None, str(e)


def get_match_info(saishi_id: str):
    """获取比赛基本信息"""
    try:
        import requests
        from bs4 import BeautifulSoup

        url = f"https://www.zhibo8.com/match{saishi_id}v.htm"
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")
        title = soup.title.string if soup.title else ""
        if "vs" in title:
            parts = title.split("vs")
            return parts[0].strip(), parts[1].strip().split("-")[0].strip()
    except:
        pass
    return "?", "?"


def main():
    # 读配置
    saishi_id = ""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE) as f:
                saishi_id = json.load(f).get("saishi_id", "")
        except:
            pass

    if not saishi_id:
        print("⚽ wc | color=gray")
        print("---")
        print("未配置比赛 | color=gray")
        print("---")
        print("配置: wc-live menu set <序号> | terminal=true | color=blue")
        return

    home, away = get_match_info(saishi_id)
    latest, error = get_live_data(saishi_id)

    if error:
        print(f"⚽ {home[:3]} vs {away[:3]} | color=yellow")
        print("---")
        print(f"⚠️ {error} | color=red")
        return

    # 解析
    pid_text = latest.get("pid_text", "")
    home_score = latest.get("home_score", "0")
    visit_score = latest.get("visit_score", "0")
    live_text = latest.get("live_text", "").strip()
    live_time = latest.get("live_ptime", "")
    user_chn = latest.get("user_chn", "")

    score = f"{home_score or '0'}-{visit_score or '0'}"

    if len(live_text) > 40:
        live_text = live_text[:37] + "..."

    # 菜单栏：比分 + 比赛时间 + 简短文字
    menu_parts = [f"⚽ {score}"]
    if live_time:
        menu_parts.append(live_time)
    if live_text:
        menu_parts.append(live_text[:20])
    menu_text = " | ".join(menu_parts)
    if len(menu_text) > 55:
        menu_text = menu_text[:52] + "..."

    print(menu_text)
    print("---")

    # 展开信息
    print(f"{home} vs {away} | color=white")
    print(f"比分: {score} | color=yellow")
    if pid_text:
        print(f"时间: {pid_text} | color=cyan")
    print("---")

    # 最新文字
    if user_chn and "系統" not in user_chn:
        print(f"[{live_time}] {user_chn}: {live_text} | color=white")
    else:
        print(f"[{live_time}] {live_text} | color=white")

    print("---")
    print(f"刷新 | refresh=true | color=green")
    print(f"终端打开 | bash='cd {SCRAPER_DIR} && .venv/bin/python3 wc-live {saishi_id}' | terminal=true | color=blue")
    print(f"直播吧网页 | bash='open https://www.zhibo8.com/match{saishi_id}v.htm' | color=purple")


if __name__ == "__main__":
    main()
