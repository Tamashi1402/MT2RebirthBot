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

// ─── Set overlay stone value ───
Blockly.Blocks['me_set_overlay_stone'] = {
  init: function() {
    this.appendValueInput("VALUE").setCheck("Number").appendField("set overlay stone to");
    this.setPreviousStatement(true, null); this.setNextStatement(true, null);
    this.setColour(180); this.setTooltip("Set the stone value displayed on the overlay");
  }
};
Blockly.Python['me_set_overlay_stone'] = function(b) {
  var val = Blockly.Python.valueToCode(b, 'VALUE', Blockly.Python.ORDER_NONE) || '0';
  return 'overlay.set_overlay(stone=' + val + ')\n';
};

// ─── Set overlay auto-str ───
Blockly.Blocks['me_set_overlay_auto_str'] = {
  init: function() {
    this.appendValueInput("TEXT").setCheck("String").appendField("set overlay auto-str to");
    this.setPreviousStatement(true, null); this.setNextStatement(true, null);
    this.setColour(180); this.setTooltip("Set the auto-strength value displayed on the overlay");
  }
};
Blockly.Python['me_set_overlay_auto_str'] = function(b) {
  var text = Blockly.Python.valueToCode(b, 'TEXT', Blockly.Python.ORDER_NONE) || "''";
  return 'overlay.set_overlay(auto_str=' + text + ')\n';
};

// ─── Show/hide overlay auto-str ───
Blockly.Blocks['me_show_overlay_auto_str'] = {
  init: function() {
    this.appendDummyInput().appendField("overlay auto-str").appendField(new Blockly.FieldDropdown([
      ["show", "True"], ["hide", "False"]
    ]), "SHOW");
    this.setPreviousStatement(true, null); this.setNextStatement(true, null);
    this.setColour(180); this.setTooltip("Show or hide the auto-strength display on the overlay");
  }
};
Blockly.Python['me_show_overlay_auto_str'] = function(b) {
  var show = b.getFieldValue('SHOW');
  return 'overlay.set_overlay(show_auto_str=' + show + ')\n';
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
Blockly.Blocks['me_draw_esp_box'] = {
  init: function() {
    this.appendValueInput("ID").setCheck("String").appendField("draw ESP box id");
    this.appendValueInput("X1").setCheck("Number").appendField("x1");
    this.appendValueInput("Y1").setCheck("Number").appendField("y1");
    this.appendValueInput("X2").setCheck("Number").appendField("x2");
    this.appendValueInput("Y2").setCheck("Number").appendField("y2");
    this.appendValueInput("R").setCheck("Number").appendField("R");
    this.appendValueInput("G").setCheck("Number").appendField("G");
    this.appendValueInput("B").setCheck("Number").appendField("B");
    this.appendValueInput("A").setCheck("Number").appendField("A");
    this.appendValueInput("LABEL").setCheck("String").appendField("label");
    this.setInputsInline(false);
    this.setPreviousStatement(true, null); this.setNextStatement(true, null);
    this.setColour(180); this.setTooltip("Draw or update a named ESP box with RGBA color (0-255 each). Same ID = update existing box.");
  }
};
Blockly.Python['me_draw_esp_box'] = function(b) {
  var id = Blockly.Python.valueToCode(b, 'ID', Blockly.Python.ORDER_NONE) || "''";
  var x1 = Blockly.Python.valueToCode(b, 'X1', Blockly.Python.ORDER_NONE) || '0';
  var y1 = Blockly.Python.valueToCode(b, 'Y1', Blockly.Python.ORDER_NONE) || '0';
  var x2 = Blockly.Python.valueToCode(b, 'X2', Blockly.Python.ORDER_NONE) || '0';
  var y2 = Blockly.Python.valueToCode(b, 'Y2', Blockly.Python.ORDER_NONE) || '0';
  var r = Blockly.Python.valueToCode(b, 'R', Blockly.Python.ORDER_NONE) || '0';
  var g = Blockly.Python.valueToCode(b, 'G', Blockly.Python.ORDER_NONE) || '255';
  var bb = Blockly.Python.valueToCode(b, 'B', Blockly.Python.ORDER_NONE) || '0';
  var a = Blockly.Python.valueToCode(b, 'A', Blockly.Python.ORDER_NONE) || '255';
  var label = Blockly.Python.valueToCode(b, 'LABEL', Blockly.Python.ORDER_NONE) || "''";
  return 'overlay.set_named_box(' + id + ', x1=' + x1 + ', y1=' + y1 + ', x2=' + x2 + ', y2=' + y2 +
         ', r=' + r + ', g=' + g + ', b=' + bb + ', a=' + a + ', label=' + label + ')\n';
};

// ─── Clear ESP box by ID ───
Blockly.Blocks['me_clear_esp_box'] = {
  init: function() {
    this.appendValueInput("ID").setCheck("String").appendField("clear ESP box id");
    this.setPreviousStatement(true, null); this.setNextStatement(true, null);
    this.setColour(180); this.setTooltip("Remove a single ESP box by its string ID");
  }
};
Blockly.Python['me_clear_esp_box'] = function(b) {
  var id = Blockly.Python.valueToCode(b, 'ID', Blockly.Python.ORDER_NONE) || "''";
  return 'overlay.clear_named_box(' + id + ')\n';
};

// ─── Clear all ESP boxes ───
Blockly.Blocks['me_clear_all_esp'] = {
  init: function() {
    this.appendDummyInput().appendField("clear all ESP boxes");
    this.setPreviousStatement(true, null); this.setNextStatement(true, null);
    this.setColour(180); this.setTooltip("Remove all named ESP boxes from the overlay");
  }
};
Blockly.Python['me_clear_all_esp'] = function(b) {
  return 'overlay.clear_all_named_boxes()\n';
};
