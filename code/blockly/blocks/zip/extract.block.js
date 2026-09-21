// Block: pcr_zip_extract — extract zip to directory
Blockly.Blocks['pcr_zip_extract'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_zip_extract",
      "message0": "extract zip %1 to %2",
      "args0": [
        { "type": "input_value", "name": "ZIP_PATH", "check": ["String", "RESLOC"] },
        { "type": "input_value", "name": "DEST", "check": ["String", "RESLOC"] }
      ],
      "inputsInline": true,
      "previousStatement": null, "nextStatement": null, "colour": 270,
      "tooltip": "Extract a zip archive to a directory"
    });
  }
};
Blockly.Python['pcr_zip_extract'] = function(block) {
  var zipPath = 'resolve_path(' + (Blockly.Python.valueToCode(block, 'ZIP_PATH', Blockly.Python.ORDER_NONE) || "''") + ')';
  var dest = 'resolve_path(' + (Blockly.Python.valueToCode(block, 'DEST', Blockly.Python.ORDER_NONE) || "''") + ')';
  return 'zip_extract(' + zipPath + ', ' + dest + ')\n';
};
