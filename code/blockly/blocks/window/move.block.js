Blockly.Blocks['pcr_window_move'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_window_move",
      "message0": "Move window %1 to %2",
      "args0": [
        { "type": "input_value", "name": "TITLE", "check": "String" },
        { "type": "input_value", "name": "POINT", "check": "Box" }
      ],
      "inputsInline": true,
      "previousStatement": null, "nextStatement": null, "colour": 210,
      "tooltip": "Move a window to a screen point (top-left corner)"
    });
  }
};
Blockly.Python['pcr_window_move'] = function(block) {
  var title = Blockly.Python.valueToCode(block, 'TITLE', Blockly.Python.ORDER_NONE) || "''";
  var pt = Blockly.Python.valueToCode(block, 'POINT', Blockly.Python.ORDER_NONE) || 'point(0, 0)';
  return 'window_move_pt(' + title + ', ' + pt + ')\n';
};
