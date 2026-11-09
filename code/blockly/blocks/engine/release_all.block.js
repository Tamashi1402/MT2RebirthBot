Blockly.Blocks['host_release_all'] = {
  init: function() {
    this.appendDummyInput().appendField("release all keys / mouse");
    this.setPreviousStatement(true);
    this.setNextStatement(true);
    this.setColour(40);
  }
};
Blockly.Python['host_release_all'] = function() {
  return 'macroforge.engine.functions.call("macroforge.engine.input.release_all")\n';
};
