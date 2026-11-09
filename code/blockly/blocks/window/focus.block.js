Blockly.Blocks['pcr_window_focus'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_window_focus",
      "message0": "focus window %1",
      "args0": [{ "type": "input_value", "name": "TITLE", "check": "String" }],
      "inputsInline": true,
      "previousStatement": null, "nextStatement": null, "colour": 210,
      "tooltip": "Find a window by title (partial match) and bring it to the front"
    });
  }
};
Blockly.Python['pcr_window_focus'] = function(block) {
  var title = Blockly.Python.valueToCode(block, 'TITLE', Blockly.Python.ORDER_NONE) || "''";
  return 'window_focus(' + title + ')\n';
};
