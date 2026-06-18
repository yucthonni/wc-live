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
wc-live SwiftBar 插件 — 在 Mac 菜单栏显示文字直播

安装步骤:
  1. brew install swiftbar (或从 GitHub 下载)
  2. 打开 SwiftBar，设置 Plugin Folder
  3. 把本脚本复制到 Plugin Folder
  4. 脚本会自动刷新（每10秒）

点击菜单栏图标可展开查看历史记录
"""

import json
import sys
import os
import subprocess

# ---------- 配置 ----------
# 比赛ID列表，可在 Plugin Options 中配置
# 默认显示最近有直播的比赛
DEFAULT_SAISHI_ID = os.environ.get("WC_SAISHI_ID", "")
PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))
SCRAPER_DIR = os.path.dirname(PLUGIN_DIR)

# 添加项目路径到 sys.path
if SCRAPER_DIR not in sys.path:
    sys.path.insert(0, SCRAPER_DIR)


def get_live_data(saishi_id: str):
    """获取最新文字直播数据"""
    try:
        import requests
        
        # 先找可用服务器
        servers = ["dingshi4pc", "dingshi145"]
        server = None
        for sv in servers:
            try:
                url = f"https://{sv}.qiumibao.com/livetext/data/cache/livetext/{saishi_id}/0/max_sid.json"
                resp = requests.get(url, timeout=5)
                if resp.status_code == 200:
                    server = sv
                    break
            except:
                continue
        
        if not server:
            return None, "无法连接服务器"
        
        # 获取最新数据
        url = f"https://{server}.qiumibao.com/livetext/data/cache/livetext/{saishi_id}/0/max_sid.json"
        resp = requests.get(url, timeout=5)
        max_sid = resp.json().get("max_sid", 0)
        
        if max_sid == 0:
            return None, "未开赛"
        
        # 获取最新文字
        url_id = int(max_sid / 2) * 2
        api_url = f"https://{server}.qiumibao.com/livetext/data/cache/livetext/{saishi_id}/0/lit_page_2/{url_id}.htm"
        resp = requests.get(api_url, timeout=10)
        data = resp.json()
        
        if not data:
            return None, "无数据"
        
        latest = data[-1]
        return latest, None
        
    except Exception as e:
        return None, str(e)


def get_match_info(saishi_id: str):
    """获取比赛基本信息"""
    try:
        url = f"https://www.zhibo8.com/match{saishi_id}v.htm"
        import requests
        from bs4 import BeautifulSoup
        
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")
        
        title = soup.title.string if soup.title else ""
        # 尝试解析队名
        if "vs" in title:
            parts = title.split("vs")
            return parts[0].strip(), parts[1].strip().split("-")[0].strip()
        return "主队", "客队"
    except:
        return "?", "?"


def main():
    saishi_id = DEFAULT_SAISHI_ID
    
    if not saishi_id:
        # 没配置比赛ID，显示提示
        print("⚽ wc-live | color=white")
        print("---")
        print("点击配置比赛 ID | bash='open https://github.com/yucthonni/wc-live' | color=blue")
        return
    
    # 获取比赛信息
    home, away = get_match_info(saishi_id)
    
    # 获取最新直播
    latest, error = get_live_data(saishi_id)
    
    if error:
        print(f"⚽ {home[:3]} vs {away[:3]} | color=yellow")
        print("---")
        print(f"⚠️ {error} | color=red")
        return
    
    # 解析数据
    pid_text = latest.get("pid_text", "")
    home_score = latest.get("home_score", "0")
    visit_score = latest.get("visit_score", "0")
    live_text = latest.get("live_text", "").strip()
    live_time = latest.get("live_ptime", latest.get("live_time", "")[-5:])
    user_chn = latest.get("user_chn", "")
    
    # 比分
    score = f"{home_score or '0'}-{visit_score or '0'}"
    
    # 截短文字
    if len(live_text) > 40:
        live_text = live_text[:37] + "..."
    
    # 菜单栏显示：比分 + 最新文字
    menu_text = f"⚽ {score} | {live_time} {live_text[:20]}"
    if len(menu_text) > 50:
        menu_text = menu_text[:47] + "..."
    
    print(menu_text)
    print("---")
    
    # 完整信息
    print(f"{home} vs {away} | color=white")
    print(f"比分: {score} | color=yellow")
    print(f"时间: {pid_text} | color=cyan")
    print("---")
    
    # 最新文字
    if user_chn and "系統" not in user_chn:
        print(f"[{live_time}] {user_chn}: {live_text} | color=white")
    else:
        print(f"[{live_time}] {live_text} | color=white")
    
    print("---")
    
    # 操作
    print(f"刷新 | refresh=true | color=green")
    print(f"在终端打开 | bash='cd {SCRAPER_DIR} && python3 wc-live {saishi_id}' | terminal=true | color=blue")
    print(f"打开直播吧 | bash='open https://www.zhibo8.com/match{saishi_id}v.htm' | color=purple")


if __name__ == "__main__":
    main()
