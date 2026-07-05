"""🚀 桌宠启动入口 —— 双击运行或命令行启动"""
import sys
import os

# 确保从项目根目录启动（解决相对路径问题）
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QIcon
from PySide6.QtCore import QSharedMemory
from ui.desk_pet import DeskPet


def is_already_running() -> bool:
    """检查是否已经有一个实例在运行（用共享内存实现）"""
    global _shared_memory
    _shared_memory = QSharedMemory("AIDeskPet_SingleInstance")
    if _shared_memory.attach():
        return True  # 共享内存已存在 = 已有实例在运行
    _shared_memory.create(1)
    return False


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    # 单实例检查
    if is_already_running():
        msg = QMessageBox()
        msg.setWindowTitle("AI 桌宠助手")
        msg.setText("桌宠已经在运行中啦！🐱\n看看任务栏右下角的托盘图标～")
        msg.setIcon(QMessageBox.Information)
        msg.exec()
        sys.exit(0)

    # 可选图标
    icon_path = os.path.join(os.path.dirname(__file__), "assets", "pet_default.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # 可选：命令行指定图片
    image_path = None
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        image_path = sys.argv[1]

    pet = DeskPet(image_path=image_path)
    pet.show()

    print("🐱 桌宠已启动！")
    print("  - 点击桌宠 → 对话")
    print("  - 拖拽桌宠 → 移动")
    print("  - 右键桌宠 → 菜单")
    print("  - 关闭窗口 → 退出")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
