import atexit
import contextlib
import json
import logging
import logging.config
import queue
from logging.handlers import QueueHandler, QueueListener
from pathlib import Path


def edit_all_filename_paths(tree: dict, logs_dir: Path) -> None:
    for key, val in tree.items():
        if key == "filename":
            tree[key] = str(logs_dir / val)

        elif isinstance(val, dict):
            edit_all_filename_paths(val, logs_dir)


def setup(logger_name: str, output_path: str) -> logging.Logger:
    cwd = Path(__file__).parent

    config_file = Path(cwd, "config.json")
    logs_dir = Path(output_path).parent / "logs"
    logs_dir.mkdir(exist_ok=True)

    with config_file.open(mode="r", encoding="utf-8") as f_in:
        config = json.load(f_in)

    edit_all_filename_paths(config, logs_dir)

    logging.config.dictConfig(config)

    log_queue = queue.Queue(maxsize=0)
    queue_handler = QueueHandler(log_queue)

    root_logger = logging.getLogger()
    root_logger_handlers = list(root_logger.handlers)

    # remove sync handlers to replace them with async one
    for h in root_logger_handlers:
        root_logger.removeHandler(h)

    root_logger.addHandler(queue_handler)

    remote_listener = QueueListener(log_queue, *root_logger_handlers, respect_handler_level=True)
    remote_listener.start()

    def _stop_listener() -> None:
        with contextlib.suppress(Exception):
            remote_listener.stop()
        for h in root_logger_handlers:
            with contextlib.suppress(Exception):
                h.close()

    atexit.register(_stop_listener)

    return logging.getLogger(logger_name)
