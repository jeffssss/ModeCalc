# MIDI 回调 + Queue 双线程模型

MIDI 采集与 UI 通信分属两个线程：PortMidi 回调线程（mido + python-rtmidi）负责收消息入 `queue.Queue`，asyncio 主线程（aiohttp）定期消费队列、计算和弦、推送 WebSocket。

**为何不是纯 asyncio 轮询？** `mido` 的 `iter_pending()` 在 rtmidi 后端不可用，`receive(block=False)` 一次只拿一条消息，快速琶音或密集和弦可能积压。回调模式是 PortMidi 原生推荐用法，回调函数只做 `queue.put`，几乎零开销，不丢消息。

**Queue 为何足够？** `queue.Queue` 是 Python 标准库的线程安全原语，无锁竞争。5ms asyncio 轮询间隔人耳不可感知。

**被认为但放弃的方案：**
- 纯 asyncio 轮询 `receive(block=False)`：丢消息风险
- 回调中直接做和弦计算 + WebSocket 推送：PortMidi 线程不应做 I/O 密集型操作，且需处理 GIL 和 asyncio 跨线程问题
