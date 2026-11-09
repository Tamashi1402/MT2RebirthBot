// Block: pcr_return_none — plain return (no value)
Blockly.Blocks['pcr_return_none'] = {
  init: function() {
    this.appendDummyInput().appendField("return");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour(120);
    this.setTooltip("Return from this procedure without a value");
  }
};
Blockly.Python['pcr_return_none'] = function(block) {
  return 'return\n';
};
