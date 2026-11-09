Blockly.Blocks['pcr_window_resize'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_window_resize",
      "message0": "resize window %1 to width %2 height %3",
      "args0": [
        { "type": "input_value", "name": "TITLE", "check": "String" },
        { "type": "input_value", "name": "W", "check": "Number" },
        { "type": "input_value", "name": "H", "check": "Number" }
      ],
      "inputsInline": true,
      "previousStatement": null, "nextStatement": null, "colour": 210,
      "tooltip": "Resize a window to a specific width and height"
    });
  }
};
Blockly.Python['pcr_window_resize'] = function(block) {
  var title = Blockly.Python.valueToCode(block, 'TITLE', Blockly.Python.ORDER_NONE) || "''";
  var w = Blockly.Python.valueToCode(block, 'W', Blockly.Python.ORDER_NONE) || '0';
  var h = Blockly.Python.valueToCode(block, 'H', Blockly.Python.ORDER_NONE) || '0';
  return 'window_resize(' + title + ', ' + w + ', ' + h + ')\n';
};
