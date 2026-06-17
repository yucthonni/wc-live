# wc-live — 命令行世界杯文字直播 🎯

在终端里看世界杯文字直播，摸鱼神器！基于直播吧 (zhibo8.com) 的实时数据。

## 安装

```bash
cd ~/Code/worldcup-live
source .venv/bin/activate  # 已有虚拟环境
```

如果还没装依赖：
```bash
cd ~/Code/worldcup-live
uv venv --python 3.11
source .venv/bin/activate
uv pip install requests rich beautifulsoup4 lxml
```

## 用法

```bash
# 查看今日比赛列表
python3 wc-live list

# 进入比赛文字直播（通过序号）
python3 wc-live 1

# 或者通过比赛ID
python3 wc-live 1869198

# 快捷方式（如果配置了alias）
wc list
wc 1
```

### 快捷键（直播模式）
- 进入后自动刷新，按 **Ctrl+C** 退出

## AI 解说（可选）

需要配置小米 MiMo API Key：

```bash
export MIMO_API_KEY="你的MiMo API Key"
```

然后在直播模式下程序会自动提供 AI 赛事总结。

MiMo 官网：https://mimo.mi.com

## 数据来源

- 直播吧 [zhibo8.com](https://www.zhibo8.com/)
- API: `dingshi4pc.qiumibao.com`

## 文件结构

```
~/Code/worldcup-live/
├── wc-live          # 入口脚本
├── wc               # bash 包装器
├── wc_live/
│   ├── __init__.py
│   ├── scraper.py   # 数据采集（HTTP/API）
│   ├── display.py   # 终端渲染（rich）
│   └── mimo.py      # MiMo AI 集成
├── requirements.txt
└── README.md
```
