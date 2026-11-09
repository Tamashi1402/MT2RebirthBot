// ╔══════════════════════════════════════════════╗
// ║ Block: logic_null                              ║
// ║ Category: base/logic                          ║
// ║ Desc: None / null value                       ║
// ╚══════════════════════════════════════════════╝

Blockly.Blocks['logic_null'] = {
  init: function() {
    this.appendDummyInput().appendField("none");
    this.setOutput(true, null);
    this.setColour(210);
    this.setTooltip("None / null");
  }
};

Blockly.Python['logic_null'] = function(block) {
  return ['None', Blockly.Python.ORDER_ATOMIC];
};
