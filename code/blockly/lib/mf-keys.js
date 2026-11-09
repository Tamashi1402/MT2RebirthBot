/* MacroForge key / mouse catalog — one list for Blockly stubs, Input
   sockets, and mode-settings keybinds. */
(function (g) {
  var LETTERS = "abcdefghijklmnopqrstuvwxyz".split("");
  var NUMBERS = "0123456789".split("");
  var SYSTEM = [
    ["space", "Space"], ["enter", "Enter"], ["esc", "Esc"], ["tab", "Tab"],
    ["backspace", "Backspace"], ["delete", "Delete"], ["insert", "Insert"],
    ["home", "Home"], ["end", "End"], ["page up", "Page Up"], ["page down", "Page Down"],
    ["shift", "Shift"], ["ctrl", "Ctrl"], ["alt", "Alt"], ["win", "Win"],
    ["caps lock", "Caps Lock"], ["num lock", "Num Lock"], ["scroll lock", "Scroll Lock"],
    ["print screen", "Print Screen"], ["pause", "Pause"], ["menu", "Menu"],
    ["up", "Arrow Up"], ["down", "Arrow Down"], ["left", "Arrow Left"], ["right", "Arrow Right"],
    ["comma", ","], ["period", "."], ["slash", "/"], ["semicolon", ";"],
    ["quote", "'"], ["bracket left", "["], ["bracket right", "]"],
    ["backslash", "\\"], ["minus", "-"], ["equals", "="], ["grave", "`"],
    ["any", "Any key"]
  ];
  var MOUSE = [
    ["left", "Left click"], ["right", "Right click"], ["middle", "Middle click"],
    ["x1", "Mouse 4 (X1)"], ["x2", "Mouse 5 (X2)"],
    ["wheel up", "Wheel up"], ["wheel down", "Wheel down"]
  ];

  var ALL = [];
  LETTERS.forEach(function (c) { ALL.push({ id: c, label: c.toUpperCase(), group: "letters" }); });
  NUMBERS.forEach(function (c) { ALL.push({ id: c, label: c, group: "numbers" }); });
  for (var n = 0; n <= 9; n++) ALL.push({ id: "num " + n, label: "Num " + n, group: "numbers" });
  ALL.push({ id: "num add", label: "Num +", group: "numbers" });
  ALL.push({ id: "num subtract", label: "Num -", group: "numbers" });
  ALL.push({ id: "num multiply", label: "Num *", group: "numbers" });
  ALL.push({ id: "num divide", label: "Num /", group: "numbers" });
  ALL.push({ id: "num decimal", label: "Num .", group: "numbers" });
  ALL.push({ id: "num enter", label: "Num Enter", group: "numbers" });
  for (var f = 1; f <= 24; f++) ALL.push({ id: "f" + f, label: "F" + f, group: "function" });
  SYSTEM.forEach(function (p) { ALL.push({ id: p[0], label: p[1], group: "system" }); });
  MOUSE.forEach(function (p) { ALL.push({ id: p[0], label: p[1], group: "mouse" }); });

  function flags(opt) {
    opt = opt || {};
    return {
      letters: opt.letters !== false && opt.allowLetters !== false,
      numbers: opt.numbers !== false && opt.allowNumbers !== false,
      function: opt.function !== false && opt.allowFunction !== false,
      system: opt.system !== false && opt.allowSystem !== false,
      mouse: !!(opt.mouse || opt.allowMouse)
    };
  }

  function filter(opt) {
    var f = flags(opt);
    var keysOn = f.letters || f.numbers || f.function || f.system;
    return ALL.filter(function (k) {
      if (k.group === "mouse") return f.mouse;
      return !!f[k.group];
    }).map(function (k) {
      var id = k.id;
      if (k.group === "mouse" && keysOn) id = "mouse:" + k.id;
      return { id: id, label: k.label, group: k.group };
    });
  }

  function dropdown(kind) {
    var list;
    if (kind === "mouse") list = ALL.filter(function (k) { return k.group === "mouse"; });
    else if (kind === "keys") list = ALL.filter(function (k) { return k.group !== "mouse"; });
    else if (kind === "all") list = ALL;
    else list = filter(kind || {});
    var opts = list.map(function (k) { return [k.label, k.id]; });
    if (!opts.length) opts.push(["(none)", ""]);
    return opts;
  }

  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      if (c === "&") return "&" + "amp;";
      if (c === "<") return "&" + "lt;";
      if (c === ">") return "&" + "gt;";
      if (c === "'") return "&" + "#39;";
      return "&" + "quot;";
    });
  }

  function htmlOptions(kind, selected) {
    var opts = dropdown(kind);
    var cur = String(selected == null ? "" : selected);
    var html = "";
    var seen = false;
    opts.forEach(function (o) {
      var sel = o[1] === cur ? " selected" : "";
      if (sel) seen = true;
      html += '<option value="' + esc(o[1]) + '"' + sel + ">" + esc(o[0]) + "</option>";
    });
    if (cur && !seen) {
      html = '<option value="' + esc(cur) + '" selected>' + esc(cur) + "</option>" + html;
    }
    return html;
  }

  g.MF_KEYS = { all: ALL, filter: filter, dropdown: dropdown, htmlOptions: htmlOptions, flags: flags };

  g.mfKeyCode = function (block, name, fallback) {
    if (!block || typeof Blockly === "undefined" || !Blockly.Python) {
      return JSON.stringify(fallback == null ? "space" : fallback);
    }
    var code = Blockly.Python.valueToCode(block, name, Blockly.Python.ORDER_NONE);
    if (code) return code;
    var f = block.getFieldValue(name);
    if (f != null && f !== "") return JSON.stringify(f);
    return JSON.stringify(fallback == null ? "space" : fallback);
  };

  if (typeof Blockly !== "undefined") {
    Blockly.Blocks.pcr_key = Blockly.Blocks.pcr_key || {
      init: function () {
        this.appendDummyInput().appendField(new Blockly.FieldDropdown(function () { return dropdown("keys"); }), "KEY");
        this.setOutput(true, ["Key", "String"]);
        this.setColour(40);
        this.setTooltip("A keyboard key.");
      }
    };
    Blockly.Blocks.pcr_mouse = Blockly.Blocks.pcr_mouse || {
      init: function () {
        this.appendDummyInput().appendField(new Blockly.FieldDropdown(function () { return dropdown("mouse"); }), "BUTTON");
        this.setOutput(true, ["Mouse", "Key", "String"]);
        this.setColour(40);
        this.setTooltip("A mouse button.");
      }
    };
    if (Blockly.Python) {
      Blockly.Python.pcr_key = Blockly.Python.pcr_key || function (b) {
        return [JSON.stringify(b.getFieldValue("KEY") || "space"), Blockly.Python.ORDER_ATOMIC];
      };
      Blockly.Python.pcr_mouse = Blockly.Python.pcr_mouse || function (b) {
        return [JSON.stringify(b.getFieldValue("BUTTON") || "left"), Blockly.Python.ORDER_ATOMIC];
      };
    }
  }

  function parsePyString(expr) {
    if (!expr) return null;
    var s = String(expr);
    if (s.length >= 2 && ((s.charAt(0) === '"' && s.charAt(s.length - 1) === '"') ||
        (s.charAt(0) === "'" && s.charAt(s.length - 1) === "'"))) {
      try {
        if (s.charAt(0) === '"') return JSON.parse(s);
        return s.slice(1, -1).replace(/\\'/g, "'").replace(/\\\\/g, "\\");
      } catch (e) {
        return s.slice(1, -1);
      }
    }
    return null;
  }

  g.mfJoinHotkeyCode = function (block) {
    var n = block && block.itemCount_ ? block.itemCount_ : 0;
    var parts = [];
    for (var i = 0; i < n; i++) {
      var c = Blockly.Python.valueToCode(block, "ADD" + i, Blockly.Python.ORDER_NONE);
      if (c) parts.push(c);
    }
    if (!parts.length) return ['""', Blockly.Python.ORDER_ATOMIC];
    var lits = [];
    var allLit = true;
    for (var j = 0; j < parts.length; j++) {
      var lit = parsePyString(parts[j]);
      if (lit == null) { allLit = false; break; }
      lits.push(lit);
    }
    if (allLit) {
      return [JSON.stringify(lits.join("+")), Blockly.Python.ORDER_ATOMIC];
    }
    return ['("+".join([' + parts.join(", ") + "]))", Blockly.Python.ORDER_FUNCTION_CALL];
  };
})(typeof window !== "undefined" ? window : this);

