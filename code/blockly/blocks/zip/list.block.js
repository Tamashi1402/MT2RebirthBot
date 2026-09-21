// Block: pcr_zip_list — list files in a zip
Blockly.Blocks['pcr_zip_list'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_zip_list",
      "message0": "list files in zip %1",
      "args0": [{ "type": "input_value", "name": "ZIP_PATH", "check": ["String", "RESLOC"] }],
      "inputsInline": true,
      "output": null, "colour": 270,
      "tooltip": "Return a list of file names inside a zip archive"
    });
  }
};
Blockly.Python['pcr_zip_list'] = function(block) {
  var zipPath = 'resolve_path(' + (Blockly.Python.valueToCode(block, 'ZIP_PATH', Blockly.Python.ORDER_NONE) || "''") + ')';
  return ['zip_list(' + zipPath + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};
