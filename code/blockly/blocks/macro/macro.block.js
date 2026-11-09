// ╔══════════════════════════════════════════════╗
// ║ Blocks: macro play / stop / exists — path based ║
// ║ Category: macro (legacy names, still loadable) ║
// ║ Desc: Macro files are located by PATH now:     ║
// ║ build one with "this workspace" + resource,    ║
// ║ e.g. resource "macros/mine.macro".             ║
// ╚══════════════════════════════════════════════╝

Blockly.Blocks['host_macro_play'] = {
  init: function() {
    this.appendValueInput('NAME')
      .setCheck('String')
      .appendField('macro.play');
    this.appendDummyInput()
      .appendField('wait until finished')
      .appendField(new Blockly.FieldCheckbox('TRUE'), 'WAIT');
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour(330);
    this.setTooltip('Play a .macro by path. "wait until finished" ON (default): the next block runs only after the macro is done. OFF: the macro plays in the background and the flow continues immediately.');
  }
};
Blockly.Python['host_macro_play'] = function(block) {
  var path = Blockly.Python.valueToCode(block, 'NAME', Blockly.Python.ORDER_NONE) || "''";
  var wait = String(block.getFieldValue('WAIT')).toUpperCase() === 'TRUE' ? 'True' : 'False';
  return 'macroforge.engine.functions.call("macroforge.engine.macro.play", ' + path + ', ' + wait + ')\n';
};

Blockly.Blocks['host_macro_stop'] = {
  init: function() {
    this.appendDummyInput().appendField("macro.stop");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour(0);
    this.setTooltip('Stop every playing macro.');
  }
};
Blockly.Python['host_macro_stop'] = function() {
  return 'macroforge.engine.functions.call("macroforge.engine.macro.stop")\n';
};

Blockly.Blocks['host_macro_exists'] = {
  init: function() {
    this.appendValueInput('NAME')
      .setCheck('String')
      .appendField('macro.exists');
    this.setOutput(true, "Boolean");
    this.setColour(330);
    this.setTooltip('True when a .macro file exists at the given path.');
  }
};
Blockly.Python['host_macro_exists'] = function(block) {
  var path = Blockly.Python.valueToCode(block, 'NAME', Blockly.Python.ORDER_NONE) || "''";
  var code = 'macroforge.engine.functions.call("macroforge.engine.macro.exists", ' + path + ')';
  return [code, Blockly.Python.ORDER_FUNCTION_CALL];
};
