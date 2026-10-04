"""兼容旧配置：claude mcp add mindpersona -- python <path>/platform/claude/mcp_server.py

服务端代码已移到 mindpersona/server.py。新安装请用 platform/claude/README.md 里的一行命令。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from mindpersona.server import main  # noqa: E402

if __name__ == "__main__":
    main()
