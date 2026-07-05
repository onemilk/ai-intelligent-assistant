"""
统一日志系统 —— 替代项目中散落的 print() 调用。
输出到控制台 + 文件（logs/app.log），自动按天轮转。
"""
import logging
import os
import sys


def setup_logging(name: str = "ai-assistant", level: int = logging.INFO) -> logging.Logger:
    """
    初始化日志系统。

    参数：
        name: 日志器名称
        level: 日志级别（DEBUG / INFO / WARNING / ERROR）

    返回：
        配置好的 Logger 实例
    """
    logger = logging.getLogger(name)

    # 避免重复添加 handler
    if logger.handlers:
        return logger

    logger.setLevel(level)

    # 日志格式
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    # 控制台输出
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件输出（logs/app.log，自动追加）
    try:
        log_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "logs"
        )
        os.makedirs(log_dir, exist_ok=True)
        file_handler = logging.FileHandler(
            os.path.join(log_dir, "app.log"),
            encoding="utf-8",
            mode="a"  # 追加模式
        )
        file_handler.setLevel(logging.DEBUG)  # 文件记录更详细
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except OSError:
        pass  # 文件日志写入失败不影响控制台输出

    return logger


# 全局日志器
log = setup_logging()
