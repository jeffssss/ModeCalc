/**
 * ModeCalc 前端主控
 * WebSocket 连接 → 30ms debounce → 协调三区显示
 */

(function () {
  'use strict';

  // ── 状态 ──────────────────────────────────────────
  let ws = null;
  let reconnectTimer = null;
  let debounceTimer = null;
  const RECONNECT_DELAY = 2000;

  const elChord = document.getElementById('chord-name');
  const elModePanel = document.getElementById('mode-panel');
  const elMatchesList = document.getElementById('matches-list');

  let selectedMatch = null;
  var _lastActiveNotes = [];
  var _lastModeMatches = [];
  var _lastDerivedMatches = [];

  let analysisMode = 'chord';

  // ── 分析模式切换 ──────────────────────────────────

  function getSelectedParents() {
    const boxes = document.querySelectorAll('#parent-checks input.scale-check');
    const parents = [];
    boxes.forEach(function (cb) {
      if (cb.checked) parents.push(cb.value);
    });
    return parents;
  }

  function sendAnalysisMode() {
    const parents = getSelectedParents();
    if (window.pywebview && window.pywebview.api.set_analysis_mode) {
      window.pywebview.api.set_analysis_mode(analysisMode, parents);
    } else if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        type: 'set_analysis_mode',
        mode: analysisMode,
        parents: parents,
      }));
    }
  }

  function sendPinnedScale() {
    var pcs = selectedMatch ? selectedMatch.pcs : null;
    var tonicPc = selectedMatch ? selectedMatch.tonic_pc : null;
    if (window.pywebview && window.pywebview.api.set_pinned_scale) {
      window.pywebview.api.set_pinned_scale(pcs, tonicPc);
    } else if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        type: 'set_pinned_scale',
        pcs: pcs,
        tonic_pc: tonicPc,
      }));
    }
  }

  function bindAnalysisControls() {
    document.querySelectorAll('#analysis-toggle input[name=analysis]').forEach(function (radio) {
      radio.addEventListener('change', function () {
        if (!radio.checked) return;
        analysisMode = radio.value;
        elModePanel.classList.toggle('hidden', analysisMode !== 'mode');
        if (analysisMode === 'chord') {
          selectedMatch = null;
          sendPinnedScale();
        }
        sendAnalysisMode();
      });
    });
  }

  function updateGroupCheckState(group) {
    var checks = group.querySelectorAll('.scale-check');
    var total = checks.length;
    var checked = 0;
    checks.forEach(function (cb) { if (cb.checked) checked++; });
    var gcb = group.querySelector('.group-check');
    gcb.checked = checked === total;
    gcb.indeterminate = checked > 0 && checked < total;
  }

  function initGroupControls() {
    // 组全选/取消
    document.querySelectorAll('.group-check').forEach(function (gcb) {
      gcb.addEventListener('change', function () {
        var body = this.closest('.scale-group').querySelector('.group-body');
        body.querySelectorAll('.scale-check').forEach(function (cb) {
          cb.checked = gcb.checked;
        });
        sendAnalysisMode();
      });
    });

    // 子checkbox → 更新父组状态
    document.querySelectorAll('.scale-check').forEach(function (cb) {
      cb.addEventListener('change', function () {
        updateGroupCheckState(this.closest('.scale-group'));
        sendAnalysisMode();
      });
    });

    // 折叠/展开
    document.querySelectorAll('.group-header').forEach(function (header) {
      header.addEventListener('click', function (e) {
        if (e.target.tagName === 'INPUT') return;
        var body = this.nextElementSibling;
        var toggle = this.querySelector('.group-toggle');
        body.classList.toggle('collapsed');
        toggle.classList.toggle('collapsed');
      });
    });

    // 初始化各组的 indeterminate 状态
    document.querySelectorAll('.scale-group').forEach(function (g) {
      updateGroupCheckState(g);
    });

    // 同步箭头方向与 body 折叠状态
    document.querySelectorAll('.scale-group').forEach(function (g) {
      var body = g.querySelector('.group-body');
      var toggle = g.querySelector('.group-toggle');
      if (body.classList.contains('collapsed')) {
        toggle.classList.add('collapsed');
      } else {
        toggle.classList.remove('collapsed');
      }
    });
  }

  // ── Match 点击选中调式（钢琴键盘高亮/辅助创作）─

  function onMatchClick(match) {
    if (!match.pcs || match.pcs.length === 0) return;
    if (selectedMatch && match.name === selectedMatch.name) {
      selectedMatch = null;         // toggle off
    } else {
      selectedMatch = match;        // new selection / pin
    }
    sendPinnedScale();
    _lastDerivedMatches = [];       // 等下一次推送按新固定音阶重算
    updateKeyboardHighlight();

    // re-render matches list to update pin position
    if (_lastModeMatches.length > 0 || selectedMatch) {
      renderMatches(_lastModeMatches);
    } else {
      clearMatches();
    }
  }

  function updateKeyboardHighlight() {
    var activeMidi = _lastActiveNotes;
    var scaleMidi = [];
    if (selectedMatch) {
      var pcsSet = {};
      selectedMatch.pcs.forEach(function (pc) { pcsSet[pc] = true; });
      for (var n = 21; n <= 108; n++) {
        if (pcsSet[n % 12]) scaleMidi.push(n);
      }
    }
    highlightKeys(activeMidi, scaleMidi);

    // 指板高亮：合并 active + scale MIDI，精确八度映射
    if (typeof highlightFretboardFromMidi === 'function') {
      var allMidi = [];
      var seenMidi = {};
      activeMidi.forEach(function (m) {
        if (!seenMidi[m]) { seenMidi[m] = true; allMidi.push(m); }
      });
      scaleMidi.forEach(function (m) {
        if (!seenMidi[m]) { seenMidi[m] = true; allMidi.push(m); }
      });
      highlightFretboardFromMidi(allMidi);
    }
  }

  // ── WebSocket (仅浏览器模式使用) ──────────────────

  function connect() {
    if (location.protocol === 'file:' || window.pywebview) {
      return;
    }

    if (ws && ws.readyState === WebSocket.OPEN) return;

    try {
      ws = new WebSocket(`ws://${location.host}/ws`);
    } catch (e) {
      console.error('[ws] 连接失败:', e);
      return;
    }

    ws.onopen = () => {
      sendAnalysisMode();
    };

    ws.onmessage = (e) => {
      const data = JSON.parse(e.data);
      // 非状态消息（如 MIDI 设备列表）直达处理
      if (data.type === 'midi_ports') {
        setMidiPorts(data.ports);
        return;
      }
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => updateUI(data), 30);
    };

    ws.onclose = () => {
      scheduleReconnect();
    };

    ws.onerror = () => {};
  }

  function scheduleReconnect() {
    if (reconnectTimer) return;
    reconnectTimer = setTimeout(() => {
      reconnectTimer = null;
      connect();
    }, RECONNECT_DELAY);
  }

  // ── UI 更新 (含去重) ──────────────────────────────

  var _lastDataStr = '';
  function updateUI(data) {
    var s = JSON.stringify(data);
    if (s === _lastDataStr) return;
    _lastDataStr = s;

    _lastActiveNotes = (data.active_notes || []).map(function(n) { return n.midi; });
    _lastModeMatches = data.mode_matches || [];
    _lastDerivedMatches = data.derived_matches || [];

    // 顶部始终显示和弦透镜
    if (data.result_type === 'none') {
      elChord.textContent = '';
      elChord.style.opacity = '1';
    } else if (data.result_type === 'unknown') {
      elChord.textContent = data.result?.name || '';
      elChord.style.opacity = '0.4';
    } else if (data.result) {
      elChord.textContent = data.result.name;
      elChord.style.opacity = '1';
      if (data.result_type === 'chord' && data.result.is_incomplete) {
        elChord.textContent += ' ?';
      }
    }

    // 侧栏 Matches：选中调式永远在首位，无音符也显示
    const hasNotes = (data.active_notes || []).length > 0;
    if (data.analysis_mode === 'mode' && (hasNotes || selectedMatch)) {
      renderMatches(_lastModeMatches);
    } else if (hasNotes && data.result) {
      renderMatches([{ name: data.result.name }]);
    } else {
      clearMatches();
    }

    if (typeof highlightKeys === 'function') {
      updateKeyboardHighlight();
    }

    if (typeof renderStaff === 'function') {
      renderStaff(data.active_notes || [], data.key_sig || 'C');
    }

    var susEl = document.getElementById('sustain-indicator');
    if (susEl) susEl.classList.toggle('active', !!data.sustain);

    setDebug('db-notes', (data.active_notes || []).map(function(n) { return n.midi; }).join(',') || '-');
    setDebug('db-sus', data.sustain ? 'SUS' : '');
  }

  function renderMatches(matches) {
    if (!elMatchesList) return;
    elMatchesList.innerHTML = '';

    var shown = {};

    // 选中调式：永远钉在第一条
    if (selectedMatch) {
      const li = document.createElement('li');
      li.textContent = selectedMatch.name;
      li.classList.add('selected');
      li.dataset.pcs = JSON.stringify(selectedMatch.pcs || []);
      li.addEventListener('click', function () { onMatchClick(selectedMatch); });
      elMatchesList.appendChild(li);
      shown[selectedMatch.name] = true;
    }

    // 派生调式（红音触发）：紧跟在固定调式下方
    _lastDerivedMatches.forEach(function (m) {
      if (shown[m.name]) return;
      shown[m.name] = true;
      const li = document.createElement('li');
      li.textContent = '↳ ' + m.name;
      li.classList.add('derived');
      li.dataset.pcs = JSON.stringify(m.pcs || []);
      li.addEventListener('click', function () { onMatchClick(m); });
      elMatchesList.appendChild(li);
    });

    // 其余匹配（跳过已显示的固定/派生项）
    matches.forEach(function (m) {
      if (shown[m.name]) return;
      shown[m.name] = true;
      const li = document.createElement('li');
      li.textContent = m.name;
      li.dataset.pcs = JSON.stringify(m.pcs || []);
      li.addEventListener('click', function () { onMatchClick(m); });
      elMatchesList.appendChild(li);
    });
  }

  function clearMatches() {
    if (elMatchesList) elMatchesList.innerHTML = '';
  }

  // ── 调试栏 ──────────────────────────────────────────

  function setDebug(id, text) {
    var el = document.getElementById(id);
    if (el) el.textContent = text;
  }
  window._debugBar = function(text) { setDebug('db-midi', text); };

  // ── 调号更改 ──────────────────────────────────────────

  function bindKeySelector() {
    var el = document.getElementById('key-select');
    if (!el) return;
    el.addEventListener('change', function () {
      var keySig = el.value;
      if (window.pywebview && window.pywebview.api.set_key_signature) {
        window.pywebview.api.set_key_signature(keySig);
      }
    });
  }

  // ── 菜单栏 ──────────────────────────────────────────

  function syncKeyMenuSelection() {
    var el = document.getElementById('key-select');
    var val = el ? el.value : 'C';
    document.querySelectorAll('#key-menu .menu-option').forEach(function (opt) {
      opt.classList.toggle('selected', opt.dataset.value === val);
    });
  }

  function bindMenuBar() {
    // 点击触发按钮 → 切换下拉
    document.querySelectorAll('.menu-trigger').forEach(function (btn) {
      btn.addEventListener('click', function (e) {
        e.stopPropagation();
        var menuId = btn.dataset.menu;
        var dropdown = document.getElementById(menuId);
        var isOpen = dropdown.classList.contains('open');

        // 关闭其他所有下拉
        document.querySelectorAll('.menu-dropdown.open').forEach(function (d) {
          d.classList.remove('open');
        });
        document.querySelectorAll('.menu-trigger.active').forEach(function (b) {
          b.classList.remove('active');
        });

        if (!isOpen) {
          dropdown.classList.add('open');
          btn.classList.add('active');
          syncKeyMenuSelection();
        }
      });
    });

    // 点击调性选项
    document.querySelectorAll('#key-menu .menu-option').forEach(function (opt) {
      opt.addEventListener('click', function () {
        var val = opt.dataset.value;
        var sel = document.getElementById('key-select');
        if (sel) {
          sel.value = val;
          sel.dispatchEvent(new Event('change'));
        }
        closeAllMenus();
      });
    });

    // 点击帮助选项
    document.querySelectorAll('#help-menu .menu-option').forEach(function (opt) {
      opt.addEventListener('click', function () {
        var action = opt.dataset.action;
        closeAllMenus();
        if (action === 'usage-guide') {
          var overlay = document.getElementById('modal-overlay');
          if (overlay) overlay.classList.remove('hidden');
        }
      });
    });

    // 点击外部 → 关闭所有
    document.addEventListener('click', function () {
      closeAllMenus();
    });
  }

  // ── 帮助弹窗 ──────────────────────────────────────────

  function bindModal() {
    var overlay = document.getElementById('modal-overlay');
    var closeBtn = document.getElementById('modal-close');
    if (!overlay || !closeBtn) return;
    closeBtn.addEventListener('click', function () { overlay.classList.add('hidden'); });
    overlay.addEventListener('click', function (e) {
      if (e.target === overlay) overlay.classList.add('hidden');
    });
  }

  function closeAllMenus() {
    document.querySelectorAll('.menu-dropdown.open').forEach(function (d) {
      d.classList.remove('open');
    });
    document.querySelectorAll('.menu-trigger.active').forEach(function (b) {
      b.classList.remove('active');
    });
  }

  // ── MIDI 设备列表 ──────────────────────────────────

  var _midiPorts = [];
  var _selectedMidiPort = null; // null = All

  function setMidiPorts(ports) {
    _midiPorts = ports;
    var menu = document.getElementById('midi-menu');
    if (!menu) return;
    menu.innerHTML = '';

    // All MIDI Input
    var all = document.createElement('div');
    all.className = 'menu-option';
    all.dataset.port = '';
    all.textContent = 'All MIDI Input';
    menu.appendChild(all);

    // 分割线
    var sep = document.createElement('div');
    sep.className = 'menu-separator';
    menu.appendChild(sep);

    // 具体设备
    ports.forEach(function (name) {
      var opt = document.createElement('div');
      opt.className = 'menu-option';
      opt.dataset.port = name;
      opt.textContent = name;
      menu.appendChild(opt);
    });

    // 绑定点击
    menu.querySelectorAll('.menu-option').forEach(function (opt) {
      opt.addEventListener('click', function () {
        var port = opt.dataset.port;
        selectMidiPort(port);
        closeAllMenus();
      });
    });

    // 标记当前选中
    syncMidiMenuSelection();
  }

  function selectMidiPort(port) {
    _selectedMidiPort = port || null; // '' → null = All
    if (window.pywebview && window.pywebview.api.select_midi_port) {
      window.pywebview.api.select_midi_port(_selectedMidiPort);
    } else if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'select_midi_port', port: _selectedMidiPort }));
    }
    syncMidiMenuSelection();
  }

  function syncMidiMenuSelection() {
    var menu = document.getElementById('midi-menu');
    if (!menu) return;
    menu.querySelectorAll('.menu-option').forEach(function (opt) {
      var val = opt.dataset.port || null;
      opt.classList.toggle('selected', val === _selectedMidiPort);
    });
  }

  // 暴露给 pywebview evaluate_js
  window.setMidiPorts = setMidiPorts;

  window.updateUI = updateUI;

  // ── 设置持久化（母音阶勾选） ──────────────────────

  function applySavedParents(parents) {
    var wanted = {};
    parents.forEach(function (p) { wanted[p] = true; });
    document.querySelectorAll('#parent-checks input.scale-check').forEach(function (cb) {
      cb.checked = !!wanted[cb.value];
    });
    document.querySelectorAll('.scale-group').forEach(function (g) {
      updateGroupCheckState(g);
    });
  }
  window.applySavedParents = applySavedParents;

  function loadSavedParents() {
    if (!(window.pywebview && window.pywebview.api && window.pywebview.api.get_settings)) return;
    try {
      window.pywebview.api.get_settings().then(function (s) {
        if (s && Array.isArray(s.parents)) applySavedParents(s.parents);
      }).catch(function () {});
    } catch (e) { /* bridge 未就绪，等 pywebviewready */ }
  }

  window.addEventListener('pywebviewready', loadSavedParents);
  loadSavedParents();

  bindAnalysisControls();
  initGroupControls();
  bindKeySelector();
  bindMenuBar();
  bindModal();
  connect();

})();
