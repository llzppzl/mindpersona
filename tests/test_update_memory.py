import pytest
import tempfile
import shutil
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from mindpersona import server as mcp_server
from mindpersona.server import append_to_customized, get_customized_template, MEMORY_DIR

@pytest.fixture
def temp_memory_dir():
    """创建临时 memory 目录用于测试"""
    temp_dir = tempfile.mkdtemp()
    original_dir = MEMORY_DIR

    # 临时替换 MEMORY_DIR
    mcp_server.MEMORY_DIR = Path(temp_dir)

    yield Path(temp_dir)

    # 恢复
    mcp_server.MEMORY_DIR = original_dir
    shutil.rmtree(temp_dir)

def test_append_creates_new_file(temp_memory_dir):
    """文件不存在时，应该创建并写入第一条反馈"""
    success, msg = append_to_customized("intj", "用户觉得回复太啰嗦")
    assert success
    assert (temp_memory_dir / "customized-intj.md").exists()

def test_append_adds_entry_to_existing_file(temp_memory_dir):
    """文件存在时，应该追加到 ## 你的私人调整 部分"""
    # 先创建文件
    append_to_customized("intj", "第一次反馈")

    # 再追加
    success, msg = append_to_customized("intj", "第二次反馈")
    assert success

    content = (temp_memory_dir / "customized-intj.md").read_text(encoding="utf-8")
    assert "第一次反馈" in content
    assert "第二次反馈" in content

def test_template_contains_correct_format():
    """模板生成应该包含正确格式"""
    template = get_customized_template("INTJ", "测试反馈")
    assert "# INTJ 进化版" in template
    assert "## 你的私人调整" in template
    assert "测试反馈" in template
    assert "[20" in template  # timestamp