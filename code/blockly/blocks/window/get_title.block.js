Blockly.Blocks['pcr_window_get_title'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_window_get_title",
      "message0": "get active window title",
      "output": "String", "colour": 160,
      "tooltip": "Return the title of the currently active/focused window"
    });
  }
};
Blockly.Python['pcr_window_get_title'] = function(block) {
  return ['window_get_title()', Blockly.Python.ORDER_FUNCTION_CALL];
};
