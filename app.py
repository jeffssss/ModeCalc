"""ModeCalc 桌面版 — pywebview 主入口"""

import json
import logging
import os
import sys
import threading
import time
from pathlib import Path

import webview

from chord_engine import analyze, note_info
from midi_handler import MidiHandler
from scale_library import ScaleLibrary

UI_INTERVAL = 0.03  # 30ms 固定推送间隔

# ── 日志 ────────────────────────────────────────────

LOG_FILE = os.environ.get("MODECALC_LOG") or os.path.join(
    os.environ.get("TEMP", "."), "ModeCalc_debug.log"
)

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    force=True,
)
log = logging.getLogger("modecalc")


class MidiState:
    """MIDI 采集 + 状态管理"""

    def __init__(self):
        self.handler = MidiHandler()
        self._analysis_mode = "chord"
        self.library = ScaleLibrary.load()
        self._pinned_pcs: frozenset[int] = frozenset()
        self._pinned_tonic: int | None = None
        self._key_sig = "C"

    def set_analysis_mode(self, mode: str, parents: list[str] | None = None):
        if mode not in ("chord", "mode"):
            raise ValueError(f"无效 analysis_mode: {mode}")
        self._analysis_mode = mode

    def set_key_signature(self, key_sig: str):
        self._key_sig = key_sig

    def set_pinned_scale(self, pcs=None, tonic_pc=None):
        """记录/清除当前固定的调式音阶（前端点击 Matches 时同步）。"""
        if not pcs:
            self._pinned_pcs = frozenset()
            self._pinned_tonic = None
            return
        self._pinned_pcs = frozenset(int(p) % 12 for p in pcs)
        self._pinned_tonic = None if tonic_pc is None else int(tonic_pc) % 12

    def get_state(self) -> dict:
        """消费队列 → 返回当前完整和弦数据。每次调用都处理所有新消息。"""
        active = self.handler.poll()  # 永远返回 set[int]
        result = analyze(
            active,
            analysis_mode=self._analysis_mode,
            key_sig=self._key_sig,
            pinned_pcs=self._pinned_pcs,
            pinned_tonic=self._pinned_tonic,
            scales=self.library.detection_rows(),
        )
        result["active_notes"] = [note_info(n, self._key_sig) for n in sorted(active)]
        result["sustain"] = self.handler.sustain
        return result


class Api:
    def __init__(self):
        self.state = MidiState()
        self._window: webview.Window | None = None

    def set_window(self, w: webview.Window):
        self._window = w

    def set_analysis_mode(self, mode: str, parents: list[str] | None = None):
        """JS → Python: 切换 Chord / Mode 视角（parents 参数保留兼容，已忽略）"""
        self.state.set_analysis_mode(mode, parents)
        log.info(f"analysis_mode={mode}")

    def set_key_signature(self, key_sig: str):
        """JS → Python: 调号变更"""
        self.state.set_key_signature(key_sig)
        log.info(f"key_sig={key_sig}")

    def get_scale_library(self):
        """JS → Python: 读取当前音阶库（含内置默认与用户改动）"""
        return self.state.library.payload()

    def set_scale_enabled(self, scale_id: str, enabled: bool):
        """JS → Python: 切换某个音阶的「使用」状态"""
        result = self.state.library.set_enabled(scale_id, enabled)
        log.info(f"scale enabled: {scale_id} = {enabled} ({result.get('ok')})")
        return result

    def set_group_enabled(self, section: str, group: str, enabled: bool):
        """JS → Python: 分组三态全选"""
        result = self.state.library.set_group_enabled(section, group, enabled)
        log.info(f"scale group: {section}/{group} = {enabled} ({result.get('ok')})")
        return result

    def update_scale(self, scale_id: str, name=None, pcs=None):
        """JS → Python: 修改音阶名称或音集"""
        result = self.state.library.update(scale_id, name=name, pcs=pcs)
        log.info(f"scale update: {scale_id} ({result.get('ok')})")
        return result

    def add_scale(self, name=None, pcs=None):
        """JS → Python: 新建自定义音阶"""
        result = self.state.library.add(name=name, pcs=pcs)
        log.info(f"scale add: {result.get('new_id')} ({result.get('ok')})")
        return result

    def delete_scale(self, scale_id: str):
        """JS → Python: 删除音阶（内置可恢复，自定义永久删除）"""
        result = self.state.library.delete(scale_id)
        log.info(f"scale delete: {scale_id} ({result.get('ok')})")
        return result

    def reset_scale_library(self):
        """JS → Python: 恢复内置默认，保留自定义音阶"""
        result = self.state.library.reset()
        log.info(f"scale library reset ({result.get('ok')})")
        return result

    def set_pinned_scale(self, pcs=None, tonic_pc=None):
        """JS → Python: 固定/取消固定某个调式音阶"""
        self.state.set_pinned_scale(pcs, tonic_pc)

    def list_midi_ports(self):
        """JS → Python: 获取 MIDI 设备列表"""
        return MidiHandler.list_ports()

    def select_midi_port(self, port_name: str | None = None):
        """JS → Python: 选择 MIDI 输入设备"""
        self.state.handler.select_port(port_name)
        log.info(f"MIDI port selected: {port_name or 'All'}")

    def quit_app(self):
        log.info("用户退出")
        sys.exit(0)


def midi_loop(state: MidiState, window: webview.Window):
    """后台线程: 每次醒来都拉取当前 MIDI 状态并推送。无去重 — 去重交给 JS。"""
    last_push = 0.0
    log.info("midi_loop 启动")
    while True:
        try:
            data = state.get_state()
            now = time.monotonic()
            if now - last_push >= UI_INTERVAL:
                notes = data.get("active_notes", [])
                if notes:
                    r = data.get("result") or {}
                    label = r.get("name", "?")
                    log.info(f"音符: {[n['midi'] for n in notes]} [{label}]")
                js = f'window.updateUI({json.dumps(data)})'
                try:
                    window.evaluate_js(js)
                except Exception as e:
                    log.warning(f"evaluate_js: {e}")
                last_push = now
        except Exception as e:
            log.error(f"循环错误: {e}", exc_info=True)
        time.sleep(0.005)  # 5ms 睡眠


def _startup(api: Api, window: webview.Window):
    log.info("_startup")
    api.set_window(window)

    try:
        api.state.handler.open(None)
        log.info(f"MIDI 已连接")
        _push_debug(window, "MIDI: 已连接")
    except Exception as e:
        log.warning(f"MIDI 无设备: {e}")
        _push_debug(window, f"MIDI: 无设备")

    # 推送 MIDI 设备列表给前端
    ports = MidiHandler.list_ports()
    log.info(f"MIDI 设备: {ports}")
    try:
        window.evaluate_js(f'setMidiPorts({json.dumps(ports)})')
    except Exception:
        pass

    t = threading.Thread(target=midi_loop, args=(api.state, window), daemon=True)
    t.start()


def _push_debug(window: webview.Window, text: str):
    try:
        window.evaluate_js(f'window._debugBar("{text}")')
    except Exception:
        pass


def main():
    log.info("=" * 40)
    log.info(f"ModeCalc 启动 | Log: {LOG_FILE}")

    api = Api()

    html_path = (Path(__file__).parent / "static" / "index.html").resolve()
    if not html_path.is_file():
        log.fatal(f"缺少 index.html: {html_path}")
        sys.exit(1)

    window = webview.create_window(
        "ModeCalc",
        url=html_path.as_uri(),
        js_api=api,
        width=1200,
        height=720,
        resizable=False,
    )

    try:
        webview.start(func=lambda: _startup(api, window), debug=False)
    finally:
        api.state.handler.close()


if __name__ == "__main__":
    main()
