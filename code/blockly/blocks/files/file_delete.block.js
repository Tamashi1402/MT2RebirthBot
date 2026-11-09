// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_file_delete                          ║
// ║ Category: file_manager                        ║
// ║ Source: MCreator File Manager plugin           ║
// ║ Desc: Delete a file                           ║
// ╚══════════════════════════════════════════════╝

// ─── Definition ───
Blockly.Blocks['pcr_file_delete'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_file_delete",
      "message0": "Delete file %1",
      "args0": [
        { "type": "input_value", "name": "PATH", "check": ["String", "RESLOC"] }
      ],
      "previousStatement": null,
      "nextStatement": null,
      "colour": 270,
      "tooltip": "Delete a file from disk"
    });
  }
};

// ─── Python Generator ───
Blockly.Python['pcr_file_delete'] = function(block) {
  var path = 'resolve_path(' + (Blockly.Python.valueToCode(block, 'PATH', Blockly.Python.ORDER_NONE) || "''") + ')';
  return 'os.remove(' + path + ')\n';
};
