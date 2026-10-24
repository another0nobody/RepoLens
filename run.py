"""RepoLens 启动脚本。

用法（在项目目录下）：

    python run.py            # 启动后手动打开 http://127.0.0.1:8765
    python run.py --open     # 启动并自动打开浏览器
    python run.py --port 9000

如果你的电脑上有多个 Python，请用装了依赖的那个，例如：

    ..\\.venv\\Scripts\\python.exe run.py --open
"""

from __future__ import annotations

import argparse
import sys
import threading
import time
import webbrowser

from repolens import __version__, config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="RepoLens：用 LangChain Agent 分析代码仓技术栈")
    parser.add_argument("--host", default=config.HOST, help=f"监听地址（默认 {config.HOST}）")
    parser.add_argument("--port", type=int, default=config.PORT, help=f"端口（默认 {config.PORT}）")
    parser.add_argument("--open", action="store_true", help="启动后自动打开浏览器")
    return parser.parse_args()


def main() -> int:
    if sys.version_info < (3, 11):
        print("需要 Python 3.11 或更高版本（本项目用到了 tomllib）。")
        print(f"当前版本：{sys.version.split()[0]}")
        return 1

    args = parse_args()

    print("=" * 62)
    print(f"  RepoLens v{__version__} · 代码仓技术栈侦探")
    print("  你的第一个 LangChain Agent 项目")
    print("=" * 62)

    cfg = config.load_model_config()
    if cfg.available:
        print(f"  模型：{cfg.display_name}（已配置，AI 解读开启）")
    else:
        print("  模型：未配置 API Key —— 仍可使用规则扫描，但不会有 AI 解读")
        print("        请复制 .env.example 为 .env，填入 GLM_API_KEY 或 DEEPSEEK_API_KEY")

    from repolens.server import create_server

    try:
        server = create_server(args.host, args.port)
    except RuntimeError as exc:
        print(f"\n启动失败：{exc}")
        return 1

    host, port = server.server_address[:2]
    display_host = "127.0.0.1" if host in {"0.0.0.0", "::"} else host
    url = f"http://{display_host}:{port}"
    print(f"\n  打开网页：{url}")
    print("  按 Ctrl+C 停止服务\n")

    if args.open:
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n正在关闭 RepoLens…")
    finally:
        server.server_close()
        # 给后台分析线程一点点收尾时间（它们是 daemon 线程，不会阻塞退出）。
        time.sleep(0.2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
