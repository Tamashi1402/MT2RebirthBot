Blockly.Blocks['pcr_return_text'] = {
  init: function() {
    this.appendDummyInput()
      .appendField("return text")
      .appendField(new Blockly.FieldTextInput(""), "VALUE");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour(160);
    this.setTooltip("Return a text value from this procedure");
  }
};
Blockly.Python['pcr_return_text'] = function(block) {
  var val = block.getFieldValue('VALUE') || '';
  return "return " + JSON.stringify(val) + "\n";
};
