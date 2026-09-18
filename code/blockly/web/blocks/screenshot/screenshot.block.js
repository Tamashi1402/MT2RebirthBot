// ╔══════════════════════════════════════════════╗
// ║ Screenshot blocks — capture screen regions    ║
// ║ Ported from MacroEngine, adapted for MT2 bot   ║
// ╚══════════════════════════════════════════════╝

// ─── Save screenshot to file ───
Blockly.Blocks['me_screenshot_full'] = {
  init: function() {
    this.appendValueInput("PATH").setCheck("String").appendField("save screenshot to");
    this.setPreviousStatement(true, null); this.setNextStatement(true, null);
    this.setColour(20); this.setTooltip("Capture the full screen and save to a file");
  }
};
Blockly.Python['me_screenshot_full'] = function(b) {
  var path = Blockly.Python.valueToCode(b, 'PATH', Blockly.Python.ORDER_NONE) || "''";
  return 'screen.save_debug_fullscreen(' + path + ')\n';
};

// ─── Capture full screen to variable ───
Blockly.Blocks['me_screenshot_full_var'] = {
  init: function() {
    this.appendDummyInput().appendField("screenshot of screen");
    this.setOutput(true, null); this.setColour(20);
    this.setTooltip("Capture the full screen as an image object");
  }
};
Blockly.Python['me_screenshot_full_var'] = function(b) {
  return ['screen.grab_full_screen()', Blockly.Python.ORDER_FUNCTION_CALL];
};

// ─── Capture screen region to variable ───
Blockly.Blocks['me_screenshot_region'] = {
  init: function() {
    this.appendValueInput("X").setCheck("Number").appendField("screenshot at x");
    this.appendValueInput("Y").setCheck("Number").appendField("y");
    this.appendValueInput("W").setCheck("Number").appendField("width");
    this.appendValueInput("H").setCheck("Number").appendField("height");
    this.setInputsInline(true);
    this.setOutput(true, null); this.setColour(20);
    this.setTooltip("Capture a screen region as an image object");
  }
};
Blockly.Python['me_screenshot_region'] = function(b) {
  var x = Blockly.Python.valueToCode(b, 'X', Blockly.Python.ORDER_NONE) || '0';
  var y = Blockly.Python.valueToCode(b, 'Y', Blockly.Python.ORDER_NONE) || '0';
  var w = Blockly.Python.valueToCode(b, 'W', Blockly.Python.ORDER_NONE) || '0';
  var h = Blockly.Python.valueToCode(b, 'H', Blockly.Python.ORDER_NONE) || '0';
  return ['screen.grab_region((' + x + ', ' + y + ', ' + w + ', ' + h + '))', Blockly.Python.ORDER_FUNCTION_CALL];
};

// ─── Save debug image ───
Blockly.Blocks['me_save_debug'] = {
  init: function() {
    this.appendValueInput("LABEL").setCheck("String").appendField("save debug image");
    this.setPreviousStatement(true, null); this.setNextStatement(true, null);
    this.setColour(20); this.setTooltip("Save a debug screenshot with a label for troubleshooting");
  }
};
Blockly.Python['me_save_debug'] = function(b) {
  var label = Blockly.Python.valueToCode(b, 'LABEL', Blockly.Python.ORDER_NONE) || "''";
  return 'screen.save_debug_fullscreen(' + label + ')\n';
};

// ─── White percent (screen region) ───
Blockly.Blocks['me_white_percent'] = {
  init: function() {
    this.appendValueInput("IMG").appendField("white % in image");
    this.setOutput(true, "Number"); this.setColour(20);
    this.setTooltip("Get the percentage of white pixels in an image");
  }
};
Blockly.Python['me_white_percent'] = function(b) {
  var img = Blockly.Python.valueToCode(b, 'IMG', Blockly.Python.ORDER_NONE) || 'None';
  return ['screen.white_percent(' + img + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};

// ─── Red percent (screen region) ───
Blockly.Blocks['me_red_percent'] = {
  init: function() {
    this.appendValueInput("IMG").appendField("red % in image");
    this.setOutput(true, "Number"); this.setColour(20);
    this.setTooltip("Get the percentage of red pixels in an image");
  }
};
Blockly.Python['me_red_percent'] = function(b) {
  var img = Blockly.Python.valueToCode(b, 'IMG', Blockly.Python.ORDER_NONE) || 'None';
  return ['screen.red_percent(' + img + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};
