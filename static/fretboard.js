/**
 * SVG 吉他指板 — 基于 traste 封装
 * MIDI 音符显示在 6 弦标准调弦指板上
 * 含品位定位点（3/5/7/9 单点，12 品双点）
 */

(function () {
  'use strict';

  const PITCH_NAMES = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B'];

  const MARKER_FRETS = [3, 5, 7, 9, 12, 15, 17];
  // 12 品双点：偏移方向（相对于弦中心）
  const DOUBLE_FRET = 12;

  let fb = null;

  /**
   * 创建吉他指板
   * @param {string} containerId
   */
  window.createFretboard = function (containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.innerHTML = '';

    // 计算宽度使高度适配容器
    const fitHeight = 135;
    // traste 内部: fret_distance = w / 16
    //              string_distance = fret_d * 0.65
    //              height = string_d * 6 + string_d * 0.5 = string_d * 6.5 = fret_d * 0.65 * 6.5
    //              w = height * 16 / (0.65 * 6.5)
    const idealWidth = fitHeight * 16 / (0.65 * 6.5);
    const containerW = container.clientWidth || 500;
    const w = Math.min(idealWidth, containerW);

    fb = new traste.Fretboard(traste.guitar, '#' + containerId, w);

    const svg = container.querySelector('svg');
    if (!svg) return;

    // 去掉 traste 内置的底边小圆点（我们自己加了弦间定位点）
    var oldMarkers = container.querySelector('g.fret_markers');
    if (oldMarkers) oldMarkers.remove();

    // SVG 自适应容器
    const vw = parseInt(svg.getAttribute('width'));
    const vh = parseInt(svg.getAttribute('height'));
    svg.removeAttribute('width');
    svg.removeAttribute('height');
    svg.setAttribute('viewBox', '0 0 ' + vw + ' ' + vh);
    svg.setAttribute('preserveAspectRatio', 'xMidYMid meet');

    // 添加品位定位点（弦之间）
    addFretMarkers(svg, w, vw, vh);
  };

  /**
   * 在指板弦间添加品位标记圆点
   * 坐标计算与 traste 内部一致
   */
  function addFretMarkers(svg, passWidth, svgW, svgH) {
    // traste 内部尺寸公式
    const fretDistance = passWidth / 16;       // fret_count=15, +1
    const stringDistance = fretDistance * 0.65;
    const marginH = fretDistance * 0.8;
    const marginV = stringDistance * 0.5;

    const ns = 'http://www.w3.org/2000/svg';
    const g = document.createElementNS(ns, 'g');
    g.setAttribute('transform', 'translate(' + marginH + ',' + marginV + ')');

    const markerR = fretDistance * 0.09;  // 内点半径，比 traste 默认稍大

    MARKER_FRETS.forEach(function (fret) {
      // X: 品与品之间居中
      var cx = fret * fretDistance - fretDistance / 2;

      if (fret === DOUBLE_FRET) {
        // 12 品：双点，分别在弦 2-3 和 弦 4-5 之间
        var offset = stringDistance * 0.6;
        addDot(g, ns, cx, stringDistance * 2 - offset, markerR);
        addDot(g, ns, cx, stringDistance * 3 + offset, markerR);
      } else {
        // 单点：弦 3-4 之间居中
        addDot(g, ns, cx, stringDistance * 2.5, markerR);
      }
    });

    svg.appendChild(g);
  }

  function addDot(parent, ns, cx, cy, r) {
    var c = document.createElementNS(ns, 'circle');
    c.setAttribute('cx', cx);
    c.setAttribute('cy', cy);
    c.setAttribute('r', r);
    c.setAttribute('fill', '#444444');
    c.setAttribute('opacity', '0.7');
    parent.appendChild(c);
  }

  /**
   * 高亮指板上的音符
   * @param {string[]} noteNames - ['C','E','G']
   */
  window.highlightFretboard = function (noteNames) {
    if (!fb) return;
    fb.clearNotes();
    if (noteNames && noteNames.length > 0) {
      var seen = {};
      var unique = [];
      noteNames.forEach(function (n) {
        if (n && !seen[n]) { seen[n] = true; unique.push(n); }
      });
      fb.drawNotes(unique);
    }
  };

  // ── 吉他调弦 MIDI 开放弦（与 traste 标准调弦一致）────
  // 弦0(E4=64) 弦1(B3=59) 弦2(G3=55)
  // 弦3(D3=50) 弦4(A2=45) 弦5(E2=40)
  const OPEN_MIDI = [64, 59, 55, 50, 45, 40];
  const FRET_COUNT = 15;

  /**
   * MIDI number → 精确 (弦, 品) 映射
   * 只在正确八度的位置显示音符，避免全音高泛化
   * @param {number[]} midiNumbers
   */
  window.highlightFretboardFromMidi = function (midiNumbers) {
    if (!fb) return;
    fb.clearNotes();
    if (!midiNumbers || midiNumbers.length === 0) return;

    var seen = {};  // 去重 key: "s-f"
    midiNumbers.forEach(function (midi) {
      var name = PITCH_NAMES[midi % 12];
      for (var s = 0; s < OPEN_MIDI.length; s++) {
        var f = midi - OPEN_MIDI[s];
        if (f >= 0 && f <= FRET_COUNT) {
          var key = s + '-' + f;
          if (!seen[key]) {
            seen[key] = true;
            fb.drawNoteAtPosition(name, s, f);
          }
        }
      }
    });
  };

  /**
   * MIDI → 音名（无八度）
   */
  window.midiToNoteName = function (midi) {
    return PITCH_NAMES[midi % 12];
  };

})();
