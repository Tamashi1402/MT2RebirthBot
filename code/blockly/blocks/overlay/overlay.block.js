// ╔══════════════════════════════════════════════╗
// ║ Overlay + ESP drawing blocks — primitives only ║
// ║ Named boxes with RGBA + string IDs              ║
// ║ Build detection/dodge logic yourself            ║
// ╚══════════════════════════════════════════════╝

// ─── Set overlay header (status) ───
Blockly.Blocks['me_set_overlay_header'] = {
  init: function() {
    this.appendValueInput("TEXT").setCheck("String").appendField("set overlay header to");
    this.setPreviousStatement(true, null); this.setNextStatement(true, null);
    this.setColour(180); this.setTooltip("Set the overlay header text (status line, top-left)");
  }
};
Blockly.Python['me_set_overlay_header'] = function(b) {
  var text = Blockly.Python.valueToCode(b, 'TEXT', Blockly.Python.ORDER_NONE) || "''";
  return 'overlay.set_overlay(status=' + text + ')\n';
};

// ─── Set overlay text (goal) ───
Blockly.Blocks['me_set_overlay_text'] = {
  init: function() {
    this.appendValueInput("TEXT").setCheck("String").appendField("set overlay text to");
    this.setPreviousStatement(true, null); this.setNextStatement(true, null);
    this.setColour(180); this.setTooltip("Set the overlay body text (goal/info line)");
  }
};
Blockly.Python['me_set_overlay_text'] = function(b) {
  var text = Blockly.Python.valueToCode(b, 'TEXT', Blockly.Python.ORDER_NONE) || "''";
  return 'overlay.set_overlay(goal=' + text + ')\n';
};

// ─── Set overlay run start time ───
Blockly.Blocks['me_set_overlay_run_time'] = {
  init: function() {
    this.appendValueInput("TIME").setCheck("Number").appendField("set overlay run start time");
    this.setPreviousStatement(true, null); this.setNextStatement(true, null);
    this.setColour(180); this.setTooltip("Set the run start time for the overlay timer (0 to reset)");
  }
};
Blockly.Python['me_set_overlay_run_time'] = function(b) {
  var t = Blockly.Python.valueToCode(b, 'TIME', Blockly.Python.ORDER_NONE) || '0';
  return 'overlay.set_overlay(run_start_time=' + t + ')\n';
};

// ════════════════════════════════════════════════
// Named ESP boxes — RGBA, string IDs, independent control
// ════════════════════════════════════════════════

// ─── Draw ESP box (named, RGBA) ───
