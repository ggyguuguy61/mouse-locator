# mouse-locator

鼠标定位器 Mouse Locator v2.3 beta

## 📌 项目介绍

一款 Windows 平台轻量小工具，按下 **F2** 即可在鼠标光标位置显示醒目的橙色脉冲准星，帮助你快速找到光标位置。
适合大屏、多显示器用户。

## ✨ 功能特性

- **F2 全局热键** — 在任何应用中按下 F2 即可触发准星
- **橙色脉冲动画** — 圆圈扩散后收缩，醒目易找
- **300ms 防抖** — 连按、长按 F2 不会造成卡顿或窗口堆积
- **全屏模式** — 可选全屏显示准星
- **单实例运行** — 不会重复打开多个程序
- **系统托盘** — 关闭窗口后最小化到托盘后台运行
- **开机自启动** — 可选开机自动运行
- **液态玻璃 UI** — iOS 风格简洁界面

## 📥 下载

官网：https://ggyguuguy61.github.io/mouse-locator/

直接在官网下载安装向导，无需注册、无需登录。

## 💻 从源码运行

### 环境要求

- Windows 10 / 11
- Python 3.10+

### 步骤

```bash
# 1. 克隆仓库
git clone https://github.com/ggyguuguy61/mouse-locator.git
cd mouse-locator

# 2. 安装依赖
pip install -r requirements.txt

# 3. 运行
python main.py
```

## 📦 打包为 EXE

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name MouseLocator --collect-all pystray main.py
```

生成的 exe 在 `dist/` 目录下。

## 📝 更新日志

### v2.3 beta
- 修复安装向导关闭窗口异常问题
- 优化程序启动报错问题
- 提升光标高亮动画流畅度
- 安装前自动关闭正在运行的程序，避免文件占用
- 安装后校验文件完整性

## ⚠️ 注意

- 本软件仅支持 **Windows**
- 软件界面仅支持 **中文**
- 此下载为安装器，安装时间可能较长
- 欢迎在 Issues 中提出建议

## 📄 许可证

MIT License — 免费开源，可自由使用和修改。
