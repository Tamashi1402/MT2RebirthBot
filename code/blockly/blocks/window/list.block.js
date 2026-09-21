Blockly.Blocks['pcr_window_list'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_window_list",
      "message0": "list all window titles",
      "output": "Array", "colour": 260,
      "tooltip": "Return a list of all open window titles"
    });
  }
};
Blockly.Python['pcr_window_list'] = function(block) {
  return ['window_list()', Blockly.Python.ORDER_FUNCTION_CALL];
};
