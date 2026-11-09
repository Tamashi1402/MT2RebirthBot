// Block: pcr_zip_create — create zip from file/folder
Blockly.Blocks['pcr_zip_create'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_zip_create",
      "message0": "create zip %1 from %2",
      "args0": [
        { "type": "input_value", "name": "ZIP_PATH", "check": ["String", "RESLOC"] },
        { "type": "input_value", "name": "SOURCE", "check": ["String", "RESLOC"] }
      ],
      "inputsInline": true,
      "previousStatement": null, "nextStatement": null, "colour": 270,
      "tooltip": "Create a zip archive from a file or directory"
    });
  }
};
Blockly.Python['pcr_zip_create'] = function(block) {
  var zipPath = 'resolve_path(' + (Blockly.Python.valueToCode(block, 'ZIP_PATH', Blockly.Python.ORDER_NONE) || "''") + ')';
  var source = 'resolve_path(' + (Blockly.Python.valueToCode(block, 'SOURCE', Blockly.Python.ORDER_NONE) || "''") + ')';
  return 'zip_create(' + zipPath + ', ' + source + ')\n';
};
