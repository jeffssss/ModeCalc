/**
 * SVG 88 键钢琴键盘
 * MIDI 21 (A0) → 108 (C8)，52 白键 + 36 黑键
 */

(function () {
  'use strict';

  const FIRST_MIDI = 21;   // A0
  const LAST_MIDI = 108;   // C8
  const WHITE_PC = new Set([0, 2, 4, 5, 7, 9, 11]);  // C D E F G A B
  const TOTAL_WHITES = 52;

  let svg = null;
  let keyElements = {};     // midi → SVG element
  let whiteKeyWidth = 0;

  // ── 按键分类预计算 ───────────────────────────────

  const whiteKeys = [];     // midi numbers of white keys in order
  const blackKeys = [];     // midi numbers of black keys in order
  const whiteIndex = {};    // midi → 0-based white key index (0 = A0)
  const blackLeftWhite = {}; // midi → midi of white key to the left

  let wIdx = 0;
  for (let n = FIRST_MIDI; n <= LAST_MIDI; n++) {
    if (WHITE_PC.has(n % 12)) {
      whiteKeys.push(n);
      whiteIndex[n] = wIdx++;
    } else {
      blackKeys.push(n);
      blackLeftWhite[n] = n - 1;  // black key sits after its left neighbor white key
    }
  }

  // ── 公开 API ─────────────────────────────────────

  window.createKeyboard = function (containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const width = container.clientWidth;
    const height = container.clientHeight;
    whiteKeyWidth = width / TOTAL_WHITES;
    const blackKeyWidth = whiteKeyWidth * 0.6;
    const blackKeyHeight = height * 0.65;

    svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
    svg.setAttribute('width', width);
    svg.setAttribute('height', height);
    svg.setAttribute('preserveAspectRatio', 'none');
    container.innerHTML = '';
    container.appendChild(svg);

    // 白键
    for (const midi of whiteKeys) {
      const x = whiteIndex[midi] * whiteKeyWidth;
      const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
      rect.setAttribute('x', x);
      rect.setAttribute('y', 0);
      rect.setAttribute('width', whiteKeyWidth);
      rect.setAttribute('height', height);
      rect.setAttribute('rx', 2);
      rect.setAttribute('ry', 2);
      rect.setAttribute('fill', '#ffffff');
      rect.setAttribute('stroke', '#333333');
      rect.setAttribute('stroke-width', '0.5');
      rect.classList.add('key-white');
      svg.appendChild(rect);
      keyElements[midi] = rect;

      // C 键标注音名（C1 ~ C8）
      if (midi % 12 === 0) {
        const octave = (midi / 12 | 0) - 1;
        const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        text.setAttribute('x', x + whiteKeyWidth / 2);
        text.setAttribute('y', height - 3);
        text.setAttribute('text-anchor', 'middle');
        text.setAttribute('font-family', 'Segoe UI, system-ui, sans-serif');
        text.setAttribute('font-size', Math.min(whiteKeyWidth * 0.45, 14));
        text.setAttribute('fill', '#888');
        text.textContent = 'C' + octave;
        svg.appendChild(text);
      }
    }

    // 黑键 (z-index 通过 DOM 顺序自然在前)
    for (const midi of blackKeys) {
      const leftWhite = blackLeftWhite[midi];
      const x = (whiteIndex[leftWhite] + 1) * whiteKeyWidth - blackKeyWidth / 2;
      const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
      rect.setAttribute('x', x);
      rect.setAttribute('y', 0);
      rect.setAttribute('width', blackKeyWidth);
      rect.setAttribute('height', blackKeyHeight);
      rect.setAttribute('rx', 1);
      rect.setAttribute('ry', 1);
      rect.setAttribute('fill', '#2a2a2a');
      rect.setAttribute('stroke', '#111');
      rect.setAttribute('stroke-width', '0.5');
      rect.classList.add('key-black');
      svg.appendChild(rect);
      keyElements[midi] = rect;
    }

    // 键盘黑色外框（SVG 内部，不占用外层布局尺寸）
    const border = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    border.setAttribute('x', 0.75);
    border.setAttribute('y', 0.75);
    border.setAttribute('width', width - 1.5);
    border.setAttribute('height', height - 1.5);
    border.setAttribute('fill', 'none');
    border.setAttribute('stroke', '#000000');
    border.setAttribute('stroke-width', 1.5);
    border.setAttribute('rx', 3);
    border.setAttribute('ry', 3);
    svg.appendChild(border);
  };

  /**
   * 双状态键盘高亮
   * @param {number[]} activeMidiNumbers - 当前按下的 MIDI note numbers
   * @param {number[]} [scaleMidiNumbers] - 选中调式的 MIDI note numbers
   *
   * 按下音在选中调式内 → active（蓝）；
   * 按下音在选中调式外 → active-out（红）；
   * 未按下的调式音 → scale（浅蓝/深蓝底）。
   */
  window.highlightKeys = function (activeMidiNumbers, scaleMidiNumbers) {
    const activeSet = new Set(activeMidiNumbers);
    const scaleSet = scaleMidiNumbers && scaleMidiNumbers.length
      ? new Set(scaleMidiNumbers) : new Set();
    const hasScale = scaleMidiNumbers && scaleMidiNumbers.length > 0;

    for (const [midi, el] of Object.entries(keyElements)) {
      const m = Number(midi);
      const isActive = activeSet.has(m);
      const isScale = hasScale && scaleSet.has(m);

      if (isActive) {
        el.classList.remove('scale');
        if (hasScale && !isScale) {
          el.classList.remove('active');
          el.classList.add('active-out');
        } else {
          el.classList.add('active');
          el.classList.remove('active-out');
        }
      } else if (isScale) {
        el.classList.remove('active', 'active-out');
        el.classList.add('scale');
      } else {
        el.classList.remove('active', 'scale', 'active-out');
      }
    }
  };

})();
