"""MIDI 采集 - 回调+Queue 双线程模型"""

import queue
import mido


# 虚拟端口关键词（Windows 上过滤用）
VIRTUAL_PORT_KEYWORDS = ("Through", "Microsoft GS", "MIDI Mapper")


class MidiHandler:
    def __init__(self):
        self._queue = queue.Queue()
        self._active_notes: set[int] = set()
        self._sustained_notes: set[int] = set()  # note_off 时踏板踩着，待释放
        self._sustain: bool = False
        self._ports: list[mido.ports.BaseInput] = []

    def open(self, port_name: str | None = None):
        """打开 MIDI 输入端口。port_name=None 打开所有非虚拟端口。"""
        if port_name:
            self._ports = [mido.open_input(port_name, callback=self._callback)]
        else:
            names = mido.get_input_names()
            real = [n for n in names
                    if not any(k in n for k in VIRTUAL_PORT_KEYWORDS)]
            if not real:
                raise RuntimeError("没有可用的 MIDI 输入设备")
            self._ports = [mido.open_input(n, callback=self._callback) for n in real]
            print(f"[midi] 已打开 {len(self._ports)} 个端口: {real}")

    def _callback(self, msg):
        """PortMidi 回调线程：仅入队"""
        self._queue.put(msg)

    def poll(self) -> set[int]:
        """
        消费队列，返回当前 active_notes 快照。
        经典踏板逻辑：CC64=127 时 note_off 不释放音符，踏板松开时一并释放。
        """
        while not self._queue.empty():
            try:
                msg = self._queue.get_nowait()
            except queue.Empty:
                break

            if msg.type == "note_on" and msg.velocity > 0:
                self._active_notes.add(msg.note)
                self._sustained_notes.discard(msg.note)  # 重新按下 = 不再等待释放
            elif msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
                if self._sustain:
                    self._sustained_notes.add(msg.note)  # 踩着踏板时不实际释放，记下来
                else:
                    self._active_notes.discard(msg.note)
            elif msg.type == "control_change" and msg.control == 64:
                new_val = msg.value >= 64
                if self._sustain and not new_val:
                    # 踏板松开：释放所有被保持的音符
                    self._active_notes -= self._sustained_notes
                    self._sustained_notes.clear()
                self._sustain = new_val

        return set(self._active_notes)

    @property
    def sustain(self) -> bool:
        return self._sustain

    def active_notes(self) -> set[int]:
        """返回当前 active notes 快照"""
        return set(self._active_notes)

    def close(self):
        for p in self._ports:
            p.close()
        self._ports.clear()

    def select_port(self, port_name: str | None = None):
        """关闭当前端口，重新打开指定端口。None = 所有非虚拟端口。"""
        self.close()
        self._active_notes.clear()
        self._sustained_notes.clear()
        self._sustain = False
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break
        self.open(port_name)

    @staticmethod
    def list_ports() -> list[str]:
        """列出所有 MIDI 输入端口"""
        return mido.get_input_names()

    @staticmethod
    def list_real_ports() -> list[str]:
        """列出过滤后的物理 MIDI 端口"""
        return [n for n in mido.get_input_names()
                if not any(k in n for k in VIRTUAL_PORT_KEYWORDS)]
