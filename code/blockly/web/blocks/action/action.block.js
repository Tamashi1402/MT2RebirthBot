// ╔══════════════════════════════════════════════╗
// ║ Action blocks — generic game operations         ║
// ║ No "crater", "delve", "kraken" in block names   ║
// ╚══════════════════════════════════════════════╝

// ─── Run macro ───
Blockly.Blocks['me_run_macro'] = {
  init: function() {
    this.appendValueInput("NAME").setCheck("String").appendField("play macro");
    this.setPreviousStatement(true, null); this.setNextStatement(true, null);
    this.setColour(20); this.setTooltip("Play a .macro file by name (without extension)");
  }
};
Blockly.Python['me_run_macro'] = function(b) {
  var name = Blockly.Python.valueToCode(b, 'NAME', Blockly.Python.ORDER_NONE) || "''";
  return 'macro_runner.run_macro(' + name + ')\n';
};

// ─── Run macro (wait option) ───
Blockly.Blocks['me_run_macro_wait'] = {
  init: function() {
    this.appendValueInput("NAME").setCheck("String").appendField("play macro");
    this.appendDummyInput().appendField("and").appendField(new Blockly.FieldDropdown([
      ["wait for finish", "True"], ["don't wait", "False"]
    ]), "WAIT");
    this.setInputsInline(true);
    this.setPreviousStatement(true, null); this.setNextStatement(true, null);
    this.setColour(20); this.setTooltip("Play a macro file, choosing whether to wait for it to finish");
  }
};
Blockly.Python['me_run_macro_wait'] = function(b) {
  var name = Blockly.Python.valueToCode(b, 'NAME', Blockly.Python.ORDER_NONE) || "''";
  var wait = b.getFieldValue('WAIT');
  return 'macro_runner.run_macro(' + name + ', wait=' + wait + ')\n';
};

// ─── Stop macro ───
Blockly.Blocks['me_stop_macro'] = {
  init: function() {
    this.appendDummyInput().appendField("stop current macro");
    this.setPreviousStatement(true, null); this.setNextStatement(true, null);
    this.setColour(20); this.setTooltip("Stop the currently playing macro");
  }
};
Blockly.Python['me_stop_macro'] = function(b) {
  return 'macro_runner.stop_macro()\n';
};

// ─── Macro exists? ───
Blockly.Blocks['me_macro_exists'] = {
  init: function() {
    this.appendValueInput("NAME").setCheck("String").appendField("macro exists");
    this.setOutput(true, "Boolean"); this.setColour(20);
    this.setTooltip("Check if a macro file exists by name");
  }
};
Blockly.Python['me_macro_exists'] = function(b) {
  var name = Blockly.Python.valueToCode(b, 'NAME', Blockly.Python.ORDER_NONE) || "''";
  return ['macro_runner.macro_exists(' + name + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};

// ─── Teleport ───
Blockly.Blocks['me_teleport'] = {
  init: function() {
    this.appendValueInput("DEST").setCheck("String").appendField("teleport to");
    this.setPreviousStatement(true, null); this.setNextStatement(true, null);
    this.setColour(20); this.setTooltip("Teleport to a destination (area1-5, area7, base, cosmic)");
  }
};
Blockly.Python['me_teleport'] = function(b) {
  var dest = Blockly.Python.valueToCode(b, 'DEST', Blockly.Python.ORDER_NONE) || "''";
  return 'teleport_menu.teleport(' + dest + ')\n';
};

// ─── Menu resume ───
Blockly.Blocks['me_menu_resume'] = {
  init: function() {
    this.appendDummyInput().appendField("menu resume");
    this.setPreviousStatement(true, null); this.setNextStatement(true, null);
    this.setColour(20); this.setTooltip("Resume from the game menu (click Play)");
  }
};
Blockly.Python['me_menu_resume'] = function(b) {
  return 'bot._do_menu_resume()\n';
};

// ─── Force restart ───
Blockly.Blocks['me_force_restart'] = {
  init: function() {
    this.appendDummyInput().appendField("force restart");
    this.setPreviousStatement(true, null); this.setNextStatement(true, null);
    this.setColour(20); this.setTooltip("Force a run restart");
  }
};
Blockly.Python['me_force_restart'] = function(b) {
  return 'bot._run_macro("force_restart")\n';
};

// ─── Unlock drills ───
Blockly.Blocks['me_unlock_drills'] = {
  init: function() {
    this.appendDummyInput().appendField("unlock drills");
    this.setPreviousStatement(true, null); this.setNextStatement(true, null);
    this.setColour(20); this.setTooltip("Run the unlock drills macro");
  }
};
Blockly.Python['me_unlock_drills'] = function(b) {
  return 'bot._maybe_unlock_drills()\n';
};

// ─── Start drill loop ───
Blockly.Blocks['me_start_drills'] = {
  init: function() {
    this.appendDummyInput().appendField("start drill loop");
    this.setPreviousStatement(true, null); this.setNextStatement(true, null);
    this.setColour(20); this.setTooltip("Start the automatic drill pressing loop");
  }
};
Blockly.Python['me_start_drills'] = function(b) {
  return 'bot._start_drill_loop()\n';
};

// ─── Stop drill loop ───
Blockly.Blocks['me_stop_drills'] = {
  init: function() {
    this.appendDummyInput().appendField("stop drill loop");
    this.setPreviousStatement(true, null); this.setNextStatement(true, null);
    this.setColour(20); this.setTooltip("Stop the automatic drill pressing loop");
  }
};
Blockly.Python['me_stop_drills'] = function(b) {
  return 'bot._stop_drill_loop()\n';
};

// ─── Select loadout ───
Blockly.Blocks['me_select_loadout'] = {
  init: function() {
    this.appendDummyInput().appendField("select loadout").appendField(new Blockly.FieldDropdown([
      ["1", "1"], ["2", "2"], ["3", "3"], ["4", "4"], ["5", "5"], ["6", "6"]
    ]), "SLOT");
    this.setPreviousStatement(true, null); this.setNextStatement(true, null);
    this.setColour(20); this.setTooltip("Select a loadout slot (1-6)");
  }
};
Blockly.Python['me_select_loadout'] = function(b) {
  var slot = b.getFieldValue('SLOT');
  return 'macro_runner.run_macro("select_loadout_' + slot + '")\n';
};

// ─── Run hit macro ───
Blockly.Blocks['me_run_hit_macro'] = {
  init: function() {
    this.appendValueInput("NAME").setCheck("String").appendField("hit macro");
    this.setPreviousStatement(true, null); this.setNextStatement(true, null);
    this.setColour(20); this.setTooltip("Run a hit macro (rock_hit, meteor_hit, baserock_hit)");
  }
};
Blockly.Python['me_run_hit_macro'] = function(b) {
  var name = Blockly.Python.valueToCode(b, 'NAME', Blockly.Python.ORDER_NONE) || "''";
  return 'bot._run_hit_macro(' + name + ')\n';
};
