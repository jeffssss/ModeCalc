"""ModeCalc 后端服务 - aiohttp + WebSocket + MIDI 采集"""

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

from aiohttp import web

from chord_engine import analyze, note_info
from midi_handler import MidiHandler
from scale_library import ScaleLibrary

POLL_INTERVAL = 0.005  # 5ms MIDI 轮询
SEND_INTERVAL = 0.03   # 30ms 推送间隔 (去重已交给前端 updateUI)


# ── WebSocket 管理 ──────────────────────────────────────────

class State:
    def __init__(self):
        self.handler = MidiHandler()
        self.clients: set[web.WebSocketResponse] = set()
        self._analysis_mode = "chord"
        self._active_parents: set[str] | None = None
        self._pinned_pcs: frozenset[int] = frozenset()
        self._pinned_tonic: int | None = None
        self.library = ScaleLibrary.load()

    def set_analysis_mode(self, mode: str, parents: list[str] | None = None):
        if mode not in ("chord", "mode"):
            raise ValueError(f"无效 analysis_mode: {mode}")
        self._analysis_mode = mode
        self._active_parents = set(parents) if parents else None

    def set_pinned_scale(self, pcs=None, tonic_pc=None):
        if not pcs:
            self._pinned_pcs = frozenset()
            self._pinned_tonic = None
            return
        self._pinned_pcs = frozenset(int(p) % 12 for p in pcs)
        self._pinned_tonic = None if tonic_pc is None else int(tonic_pc) % 12

    def register(self, ws: web.WebSocketResponse):
        self.clients.add(ws)

    def unregister(self, ws: web.WebSocketResponse):
        self.clients.discard(ws)

    async def broadcast(self, data: dict):
        dead = set()
        for ws in self.clients:
            try:
                await ws.send_json(data)
            except (ConnectionResetError, ConnectionError):
                dead.add(ws)
        self.clients -= dead

    def get_state(self) -> dict:
        """消费队列 → 返回当前和弦数据。去重交给前端 updateUI。"""
        active = self.handler.poll()
        result = analyze(
            active,
            analysis_mode=self._analysis_mode,
            pinned_pcs=self._pinned_pcs,
            pinned_tonic=self._pinned_tonic,
            scales=self.library.detection_rows(),
        )
        result["active_notes"] = [note_info(n) for n in sorted(active)]
        result["sustain"] = self.handler.sustain
        return result


state = State()


# ── 路由 ────────────────────────────────────────────────────

async def websocket_handler(request: web.Request) -> web.WebSocketResponse:
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    state.register(ws)
    print(f"[ws] 客户端连接 ({len(state.clients)} 在线)")

    # 立即推送当前状态
    current = state.get_state()
    if current["result_type"] != "none" or current.get("active_notes"):
        try:
            await ws.send_json(current)
        except ConnectionResetError:
            state.unregister(ws)
            return ws

    # 推送 MIDI 设备列表
    try:
        ports = MidiHandler.list_ports()
        await ws.send_json({"type": "midi_ports", "ports": ports})
    except Exception:
        pass

    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                try:
                    payload = json.loads(msg.data)
                    ptype = payload.get("type")
                    if ptype == "set_analysis_mode":
                        state.set_analysis_mode(
                            payload.get("mode", "chord"),
                            payload.get("parents"),
                        )
                    elif ptype == "select_midi_port":
                        state.handler.select_port(payload.get("port"))
                        print(f"[midi] port selected: {payload.get('port') or 'All'}")
                    elif ptype == "set_pinned_scale":
                        state.set_pinned_scale(
                            payload.get("pcs"), payload.get("tonic_pc")
                        )
                except (json.JSONDecodeError, ValueError) as e:
                    print(f"[ws] 无效消息: {e}")
            elif msg.type == web.WSMsgType.ERROR:
                break
    finally:
        state.unregister(ws)
        print(f"[ws] 客户端断开 ({len(state.clients)} 在线)")
    return ws


async def index_handler(request: web.Request) -> web.FileResponse:
    return web.FileResponse(Path(__file__).parent / "static" / "index.html")


async def midi_loop(app: web.Application):
    """后台 MIDI 轮询任务 (30ms 推送, 去重交给前端)"""
    last_send = 0.0
    while True:
        try:
            data = state.get_state()
            now = time.monotonic()
            if now - last_send >= SEND_INTERVAL:
                await state.broadcast(data)
                last_send = now
        except Exception as e:
            print(f"[midi] 轮询错误: {e}")
        await asyncio.sleep(POLL_INTERVAL)


async def on_startup(app: web.Application):
    # 确保 MIDI 端口已打开（main 里已打开）
    if not state.handler._ports:
        print("[midi] 无 MIDI 设备，仅运行 WebSocket 服务")
    else:
        print(f"[midi] 已连接")
    asyncio.create_task(midi_loop(app))


# ── 入口 ────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="ModeCalc - MIDI 和弦实时识别")
    parser.add_argument("--port", help="MIDI 输入端口名称")
    parser.add_argument("--list", action="store_true", help="列出所有 MIDI 端口")
    parser.add_argument("--host", default="localhost", help="Web 服务绑定地址 (默认 localhost)")
    parser.add_argument("--web-port", type=int, default=8765, help="Web 服务端口 (默认 8765)")
    args = parser.parse_args()

    if args.list:
        print("可用 MIDI 输入端口:")
        for name in MidiHandler.list_ports():
            print(f"  {name}")
        print("\n过滤后 (排除虚拟端口):")
        real = MidiHandler.list_real_ports()
        if real:
            for name in real:
                print(f"  {name}")
        else:
            print("  (无)")
        return

    # 打开 MIDI 设备
    try:
        state.handler.open(args.port)
    except Exception as e:
        print(f"[警告] 无法打开 MIDI 设备: {e}")
        print("[info] 将以无 MIDI 模式运行 (WebSocket + 静态文件仍然可用)")

    app = web.Application()
    app.on_startup.append(on_startup)
    app.router.add_get("/", index_handler)
    app.router.add_get("/ws", websocket_handler)

    # 静态文件
    static_dir = Path(__file__).parent / "static"
    if static_dir.is_dir():
        app.router.add_static("/", path=str(static_dir))

    print(f"[web] 启动 http://{args.host}:{args.web_port}")
    web.run_app(app, host=args.host, port=args.web_port)


if __name__ == "__main__":
    main()
