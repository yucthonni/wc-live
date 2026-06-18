import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import * as https from 'https';

interface LiveEntry {
  live_text: string;
  live_ptime: string;
  home_score: string;
  visit_score: string;
  pid_text: string;
  user_chn: string;
  live_time: string;
}

interface WcConfig {
  saishi_id: string;
}

let statusBarItem: vscode.StatusBarItem;
let pollTimer: NodeJS.Timeout | undefined;
const CONFIG_PATH = path.join(os.homedir(), '.wc-live.json');

function readConfig(): WcConfig | undefined {
  try {
    if (fs.existsSync(CONFIG_PATH)) {
      return JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf-8'));
    }
  } catch {}
  return undefined;
}

function fetchJson(url: string): Promise<any> {
  return new Promise((resolve, reject) => {
    https.get(url, { timeout: 8000 }, (res) => {
      let data = '';
      res.on('data', (chunk) => { data += chunk; });
      res.on('end', () => {
        try { resolve(JSON.parse(data)); }
        catch (e) { reject(e); }
      });
    }).on('error', reject);
  });
}

async function getMaxSid(saishiId: string): Promise<number> {
  const url = `https://dingshi4pc.qiumibao.com/livetext/data/cache/livetext/${saishiId}/0/max_sid.json`;
  const data = await fetchJson(url);
  return parseInt(data.max_sid || '0');
}

async function getLatestEntry(saishiId: string, maxSid: number): Promise<LiveEntry | null> {
  const urlId = Math.floor(maxSid / 2) * 2;
  const url = `https://dingshi4pc.qiumibao.com/livetext/data/cache/livetext/${saishiId}/0/lit_page_2/${urlId}.htm`;
  const data = await fetchJson(url);
  if (Array.isArray(data) && data.length > 0) {
    return data[data.length - 1];
  }
  return null;
}

async function updateStatusBar() {
  const config = readConfig();
  if (!config?.saishi_id) {
    statusBarItem.text = '$(football) wc';
    statusBarItem.tooltip = 'WC Live: 未配置比赛\n运行 wc-live menu set <序号>';
    statusBarItem.command = 'wc-live.openCli';
    return;
  }

  try {
    const maxSid = await getMaxSid(config.saishi_id);
    if (maxSid === 0) {
      statusBarItem.text = '$(football) ⏳ 未开赛';
      statusBarItem.tooltip = '比赛尚未开始';
      return;
    }

    const entry = await getLatestEntry(config.saishi_id, maxSid);
    if (!entry) {
      statusBarItem.text = '$(football) 无数据';
      return;
    }

    const score = `${entry.home_score || '0'}-${entry.visit_score || '0'}`;
    const time = entry.live_ptime || '';
    const text = (entry.live_text || '').slice(0, 25);
    const user = entry.user_chn && !entry.user_chn.includes('系統') ? entry.user_chn : '';

    let display = `$(football) ${score}`;
    if (time) { display += ` | ${time}`; }
    if (user && text) { display += ` | ${user}: ${text}`; }
    else if (text) { display += ` | ${text}`; }

    // 截断过长
    if (display.length > 80) { display = display.slice(0, 77) + '...'; }

    statusBarItem.text = display;
    statusBarItem.tooltip = `[${time}] ${score} ${user}: ${entry.live_text}`;
    statusBarItem.command = 'wc-live.showMenu';
  } catch {
    statusBarItem.text = '$(football) ⚠️ 离线';
    statusBarItem.tooltip = 'WC Live: 获取数据失败';
  }
}

export function activate(context: vscode.ExtensionContext) {
  statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
  statusBarItem.text = '$(football) loading...';
  statusBarItem.tooltip = 'WC Live';
  statusBarItem.command = 'wc-live.openCli';
  statusBarItem.show();

  context.subscriptions.push(
    vscode.commands.registerCommand('wc-live.refresh', () => updateStatusBar()),

    vscode.commands.registerCommand('wc-live.switch', async () => {
      const id = await vscode.window.showInputBox({
        prompt: '输入比赛 ID (saishi_id)',
        placeHolder: '例如: 1869199'
      });
      if (id) {
        fs.writeFileSync(CONFIG_PATH, JSON.stringify({ saishi_id: id }, null, 2));
        vscode.window.showInformationMessage(`已切换到比赛: ${id}`);
        updateStatusBar();
      }
    }),

    vscode.commands.registerCommand('wc-live.openCli', () => {
      const terminal = vscode.window.createTerminal('wc-live');
      terminal.show();
      terminal.sendText('wc list');
    }),

    vscode.commands.registerCommand('wc-live.showMenu', async () => {
      const pick = await vscode.window.showQuickPick([
        { label: '🔄 刷新', command: 'wc-live.refresh' },
        { label: '🔄 切换比赛', command: 'wc-live.switch' },
        { label: '💻 打开终端', command: 'wc-live.openCli' },
      ], { placeHolder: 'WC Live' });
      if (pick) { vscode.commands.executeCommand(pick.command); }
    })
  );

  updateStatusBar();
  pollTimer = setInterval(updateStatusBar, 10000);
}

export function deactivate() {
  if (pollTimer) { clearInterval(pollTimer); }
}
