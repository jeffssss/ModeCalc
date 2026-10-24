"""ModeCalc 桌面版 — pywebview 主入口"""

import json
import logging
import os
import sys
import threading
import time
from pathlib import Path

import webview

import settings_store
from chord_engine import analyze, note_info
from midi_handler import MidiHandler
from mode_engine import ALL_PARENTS

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
        # 上次勾选的母音阶（None = 尚无记录，沿用默认）
        saved = settings_store.load_parents()
        self._saved_parents = (
            None if saved is None else [p for p in saved if p in ALL_PARENTS]
        )
        self._active_parents = (
            None if self._saved_parents is None
            else set(self._saved_parents)
        )
        self._pinned_pcs: frozenset[int] = frozenset()
        self._pinned_tonic: int | None = None
        self._key_sig = "C"

    def set_analysis_mode(self, mode: str, parents: list[str] | None = None):
        if mode not in ("chord", "mode"):
            raise ValueError(f"无效 analysis_mode: {mode}")
        self._analysis_mode = mode
        if parents is None:
            self._active_parents = None
            return
        cleaned = [p for p in parents if p in ALL_PARENTS]
        self._active_parents = set(cleaned)
        if cleaned != self._saved_parents:
            self._saved_parents = cleaned
            settings_store.save_parents(cleaned)

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
            active_parents=self._active_parents,
            key_sig=self._key_sig,
            pinned_pcs=self._pinned_pcs,
            pinned_tonic=self._pinned_tonic,
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
        """JS → Python: 切换 Chord / Mode 视角及母音阶勾选"""
        self.state.set_analysis_mode(mode, parents)
        log.info(f"analysis_mode={mode} parents={parents}")

    def set_key_signature(self, key_sig: str):
        """JS → Python: 调号变更"""
        self.state.set_key_signature(key_sig)
        log.info(f"key_sig={key_sig}")

    def get_settings(self):
        """JS → Python: 读取上次保存的用户设置（母音阶勾选）"""
        return {"parents": self.state._saved_parents}

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
