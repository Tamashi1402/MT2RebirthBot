Blockly.Blocks['pcr_window_minimize'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_window_minimize",
      "message0": "minimize window %1",
      "args0": [{ "type": "input_value", "name": "TITLE", "check": "String" }],
      "inputsInline": true,
      "previousStatement": null, "nextStatement": null, "colour": 210,
      "tooltip": "Minimize a window"
    });
  }
};
Blockly.Python['pcr_window_minimize'] = function(block) {
  var title = Blockly.Python.valueToCode(block, 'TITLE', Blockly.Python.ORDER_NONE) || "''";
  return 'window_minimize(' + title + ')\n';
};
