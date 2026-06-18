# wc-live SwiftBar 插件

在 Mac 菜单栏显示世界杯文字直播，适合上班摸鱼。

## 安装

### 1. 安装 SwiftBar

```bash
brew install --cask swiftbar
```

或从 [GitHub](https://github.com/swiftbar/SwiftBar) 下载。

### 2. 设置 Plugin Folder

1. 打开 SwiftBar
2. 点击菜单栏的 SwiftBar 图标
3. 选择 "Set Plugin Folder"
4. 选择本目录 `~/Code/worldcup-live/swiftbar/`

### 3. 配置比赛

在终端运行：

```bash
# 设置要观看的比赛 ID
defaults write com.ameba.SwiftBar WC_SAISHI_ID -string "1869199"
```

或直接编辑脚本中的 `DEFAULT_SAISHI_ID`。

### 4. 使用

- 菜单栏会显示：`⚽ 0-1 | 58'43'' 传中被铲出底线`
- 点击可展开查看详细信息
- 支持在终端打开完整直播

## 文件

- `wc-live.10s.py` - 主脚本（每10秒刷新）

## 注意

- 需要 `requests` 和 `beautifulsoup4` 依赖
- 脚本使用项目自带的 venv
