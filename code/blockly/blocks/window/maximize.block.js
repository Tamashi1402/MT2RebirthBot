Blockly.Blocks['pcr_window_maximize'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_window_maximize",
      "message0": "maximize window %1",
      "args0": [{ "type": "input_value", "name": "TITLE", "check": "String" }],
      "inputsInline": true,
      "previousStatement": null, "nextStatement": null, "colour": 210,
      "tooltip": "Maximize a window"
    });
  }
};
Blockly.Python['pcr_window_maximize'] = function(block) {
  var title = Blockly.Python.valueToCode(block, 'TITLE', Blockly.Python.ORDER_NONE) || "''";
  return 'window_maximize(' + title + ')\n';
};
