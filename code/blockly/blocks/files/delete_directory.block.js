// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_delete_directory                     ║
// ║ Category: file_manager                        ║
// ║ Source: Extra                                  ║
// ║ Desc: Delete a directory recursively         ║
// ╚══════════════════════════════════════════════╝

// ─── Definition ───
Blockly.Blocks['pcr_delete_directory'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_delete_directory",
      "message0": "Delete directory %1",
      "args0": [
        { "type": "input_value", "name": "PATH", "check": ["String", "RESLOC"] }
      ],
      "previousStatement": null,
      "nextStatement": null,
      "colour": 270,
      "tooltip": "Delete a directory and all its contents"
    });
  }
};

// ─── Python Generator ───
Blockly.Python['pcr_delete_directory'] = function(block) {
  var path = 'resolve_path(' + (Blockly.Python.valueToCode(block, 'PATH', Blockly.Python.ORDER_NONE) || "''") + ')';
  var code = 'import shutil\n';
  code += 'shutil.rmtree(' + path + ', ignore_errors=True)\n';
  return code;
};
