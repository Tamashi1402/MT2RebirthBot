// ╔══════════════════════════════════════════════╗
// ║ Input blocks — keyboard and mouse              ║
// ║ Ported from MacroEngine, adapted for MT2 bot   ║
// ╚══════════════════════════════════════════════╝

var ME_KEYS = [
  ["space","space"],["enter","enter"],["esc","esc"],["tab","tab"],["backspace","backspace"],
  ["shift","shift"],["ctrl","ctrl"],["alt","alt"],
  ["up","up"],["down","down"],["left","left"],["right","right"],
  ["a","a"],["b","b"],["c","c"],["d","d"],["e","e"],["f","f"],["g","g"],["h","h"],
  ["i","i"],["j","j"],["k","k"],["l","l"],["m","m"],["n","n"],["o","o"],["p","p"],
  ["q","q"],["r","r"],["s","s"],["t","t"],["u","u"],["v","v"],["w","w"],["x","x"],["y","y"],["z","z"],
  ["0","0"],["1","1"],["2","2"],["3","3"],["4","4"],["5","5"],["6","6"],["7","7"],["8","8"],["9","9"],
  ["f1","f1"],["f2","f2"],["f3","f3"],["f4","f4"],["f5","f5"],["f6","f6"],
  ["f7","f7"],["f8","f8"],["f9","f9"],["f10","f10"],["f11","f11"],["f12","f12"]
];
var ME_MOUSE_BTNS = [["left","left"],["right","right"],["middle","middle"]];

// ─── Press key ───
Blockly.Blocks['me_key_press'] = {
  init: function() {
    this.appendDummyInput().appendField("press key").appendField(new Blockly.FieldDropdown(ME_KEYS), "KEY");
    this.setPreviousStatement(true, null); this.setNextStatement(true, null);
    this.setColour(40); this.setTooltip("Press and release a keyboard key");
  }
};
Blockly.Python['me_key_press'] = function(b) {
  return 'keyboard.send("' + b.getFieldValue('KEY') + '")\n';
};

// ─── Key down (hold) ───
Blockly.Blocks['me_key_down'] = {
  init: function() {
    this.appendDummyInput().appendField("hold key").appendField(new Blockly.FieldDropdown(ME_KEYS), "KEY");
    this.setPreviousStatement(true, null); this.setNextStatement(true, null);
    this.setColour(40); this.setTooltip("Hold a key down");
  }
};
Blockly.Python['me_key_down'] = function(b) {
  return 'keyboard.press("' + b.getFieldValue('KEY') + '")\n';
};

// ─── Key up (release) ───
Blockly.Blocks['me_key_up'] = {
  init: function() {
    this.appendDummyInput().appendField("release key").appendField(new Blockly.FieldDropdown(ME_KEYS), "KEY");
    this.setPreviousStatement(true, null); this.setNextStatement(true, null);
    this.setColour(40); this.setTooltip("Release a held key");
  }
};
Blockly.Python['me_key_up'] = function(b) {
  return 'keyboard.release("' + b.getFieldValue('KEY') + '")\n';
};

// ─── Key is held ───
Blockly.Blocks['me_key_is_down'] = {
  init: function() {
    this.appendDummyInput().appendField("key").appendField(new Blockly.FieldDropdown(ME_KEYS), "KEY").appendField("is held");
    this.setOutput(true, "Boolean"); this.setColour(210);
    this.setTooltip("Check if a key is currently held down");
  }
};
Blockly.Python['me_key_is_down'] = function(b) {
  return ['keyboard.is_pressed("' + b.getFieldValue('KEY') + '")', Blockly.Python.ORDER_FUNCTION_CALL];
};

// ─── Type text ───
Blockly.Blocks['me_type_text'] = {
  init: function() {
    this.appendValueInput("TEXT").setCheck("String").appendField("type text");
    this.setPreviousStatement(true, null); this.setNextStatement(true, null);
    this.setColour(40); this.setTooltip("Type a string of text via keyboard");
  }
};
Blockly.Python['me_type_text'] = function(b) {
  var t = Blockly.Python.valueToCode(b, 'TEXT', Blockly.Python.ORDER_NONE) || "''";
  return 'keyboard.write(str(' + t + '))\n';
};

// ─── Hotkey (key combo) ───
Blockly.Blocks['me_hotkey'] = {
  init: function() {
    this.appendDummyInput()
      .appendField("hotkey")
      .appendField(new Blockly.FieldDropdown([
        ["ctrl","ctrl"],["shift","shift"],["alt","alt"],["ctrl+shift","ctrl+shift"],["ctrl+alt","ctrl+alt"]
      ]), "MOD")
      .appendField("+")
      .appendField(new Blockly.FieldDropdown(ME_KEYS), "KEY");
    this.setPreviousStatement(true, null); this.setNextStatement(true, null);
    this.setColour(40); this.setTooltip("Simulate pressing a key combination (e.g. Ctrl+C)");
  }
};
Blockly.Python['me_hotkey'] = function(b) {
  return 'keyboard.send("' + b.getFieldValue('MOD') + '+' + b.getFieldValue('KEY') + '")\n';
};

// ─── Mouse click ───
Blockly.Blocks['me_mouse_click'] = {
  init: function() {
    this.appendDummyInput().appendField("click").appendField(new Blockly.FieldDropdown(ME_MOUSE_BTNS), "BUTTON");
    this.setPreviousStatement(true, null); this.setNextStatement(true, null);
    this.setColour(40); this.setTooltip("Simulate a mouse click");
  }
};
Blockly.Python['me_mouse_click'] = function(b) {
  var btn = b.getFieldValue('BUTTON');
  if (btn === 'left') return 'mouse.click()\n';
  if (btn === 'right') return 'mouse.right_click()\n';
  return 'mouse.click("middle")\n';
};

// ─── Mouse down (hold) ───
Blockly.Blocks['me_mouse_down'] = {
  init: function() {
    this.appendDummyInput().appendField("hold").appendField(new Blockly.FieldDropdown(ME_MOUSE_BTNS), "BUTTON").appendField("mouse");
    this.setPreviousStatement(true, null); this.setNextStatement(true, null);
    this.setColour(40); this.setTooltip("Hold a mouse button down");
  }
};
Blockly.Python['me_mouse_down'] = function(b) {
  var btn = b.getFieldValue('BUTTON');
  if (btn === 'left') return 'mouse.press()\n';
  if (btn === 'right') return 'mouse.press("right")\n';
  return 'mouse.press("middle")\n';
};

// ─── Mouse up (release) ───
Blockly.Blocks['me_mouse_up'] = {
  init: function() {
    this.appendDummyInput().appendField("release").appendField(new Blockly.FieldDropdown(ME_MOUSE_BTNS), "BUTTON").appendField("mouse");
    this.setPreviousStatement(true, null); this.setNextStatement(true, null);
    this.setColour(40); this.setTooltip("Release a held mouse button");
  }
};
Blockly.Python['me_mouse_up'] = function(b) {
  var btn = b.getFieldValue('BUTTON');
  if (btn === 'left') return 'mouse.release()\n';
  if (btn === 'right') return 'mouse.release("right")\n';
  return 'mouse.release("middle")\n';
};

// ─── Mouse move absolute ───
Blockly.Blocks['me_mouse_move_abs'] = {
  init: function() {
    this.appendValueInput("X").setCheck("Number").appendField("move mouse to x");
    this.appendValueInput("Y").setCheck("Number").appendField("y");
    this.setInputsInline(true);
    this.setPreviousStatement(true, null); this.setNextStatement(true, null);
    this.setColour(40); this.setTooltip("Move mouse to absolute screen coordinates");
  }
};
Blockly.Python['me_mouse_move_abs'] = function(b) {
  var x = Blockly.Python.valueToCode(b, 'X', Blockly.Python.ORDER_NONE) || '0';
  var y = Blockly.Python.valueToCode(b, 'Y', Blockly.Python.ORDER_NONE) || '0';
  return 'macro_runner._mouse_move_abs(int(' + x + '), int(' + y + '))\n';
};

// ─── Mouse move relative ───
Blockly.Blocks['me_mouse_move_rel'] = {
  init: function() {
    this.appendValueInput("DX").setCheck("Number").appendField("move mouse by dx");
    this.appendValueInput("DY").setCheck("Number").appendField("dy");
    this.setInputsInline(true);
    this.setPreviousStatement(true, null); this.setNextStatement(true, null);
    this.setColour(40); this.setTooltip("Move mouse by relative offset (dx, dy)");
  }
};
Blockly.Python['me_mouse_move_rel'] = function(b) {
  var dx = Blockly.Python.valueToCode(b, 'DX', Blockly.Python.ORDER_NONE) || '0';
  var dy = Blockly.Python.valueToCode(b, 'DY', Blockly.Python.ORDER_NONE) || '0';
  return 'macro_runner._mouse_move_rel(int(' + dx + '), int(' + dy + '))\n';
};

// ─── Smooth move (sensitivity-aware) ───
Blockly.Blocks['me_smooth_move'] = {
  init: function() {
    this.appendValueInput("DX").setCheck("Number").appendField("smooth move dx");
    this.appendValueInput("DY").setCheck("Number").appendField("dy");
    this.setInputsInline(true);
    this.setPreviousStatement(true, null); this.setNextStatement(true, null);
    this.setColour(40); this.setTooltip("Sensitivity-aware relative mouse move (from .macro format)");
  }
};
Blockly.Python['me_smooth_move'] = function(b) {
  var dx = Blockly.Python.valueToCode(b, 'DX', Blockly.Python.ORDER_NONE) || '0';
  var dy = Blockly.Python.valueToCode(b, 'DY', Blockly.Python.ORDER_NONE) || '0';
  return 'macro_runner._smooth_move_rel(int(' + dx + '), int(' + dy + '))\n';
};

// ─── Mouse scroll ───
Blockly.Blocks['me_mouse_scroll'] = {
  init: function() {
    this.appendValueInput("AMOUNT").setCheck("Number").appendField("scroll mouse by");
    this.setPreviousStatement(true, null); this.setNextStatement(true, null);
    this.setColour(40); this.setTooltip("Scroll the mouse wheel (positive = up, negative = down)");
  }
};
Blockly.Python['me_mouse_scroll'] = function(b) {
  var amt = Blockly.Python.valueToCode(b, 'AMOUNT', Blockly.Python.ORDER_NONE) || '0';
  return 'mouse.wheel(int(' + amt + '))\n';
};

// ─── Get mouse position ───
Blockly.Blocks['me_get_mouse_pos'] = {
  init: function() {
    this.appendDummyInput().appendField("mouse position");
    this.setOutput(true, null); this.setColour(40);
    this.setTooltip("Get the current mouse (x, y) position");
  }
};
Blockly.Python['me_get_mouse_pos'] = function(b) {
  return ['mouse.get_position()', Blockly.Python.ORDER_FUNCTION_CALL];
};
