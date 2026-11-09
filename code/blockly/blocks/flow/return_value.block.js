// Block: pcr_return_value — return a value from a connected block
Blockly.Blocks['pcr_return_value'] = {
  init: function() {
    this.appendValueInput("VALUE")
      .setCheck(null)
      .appendField("return");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour(120);
    this.setTooltip("Return a value from this procedure (works with any type)");
  }
};
Blockly.Python['pcr_return_value'] = function(block) {
  var val = Blockly.Python.valueToCode(block, 'VALUE', Blockly.Python.ORDER_NONE) || 'None';
  return 'return ' + val + '\n';
};
