"""🚀 桌宠启动入口 —— 双击运行或命令行启动"""
import sys
import os

# 确保从项目根目录启动（解决相对路径问题）
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from ui.desk_pet import DeskPet


def main():
    # 创建 Qt 应用
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # 关闭所有窗口不退出（托盘程序风格）

    # 可选：加载图标
    icon_path = os.path.join(os.path.dirname(__file__), "assets", "pet_default.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # 可选：从命令行参数加载指定的宠物图片
    image_path = None
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        image_path = sys.argv[1]

    # 创建桌宠
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
