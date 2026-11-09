// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_create_directory                      ║
// ║ Category: file_manager                        ║
// ║ Source: Extra                                  ║
// ║ Desc: Create a directory                      ║
// ╚══════════════════════════════════════════════╝

// ─── Definition ───
Blockly.Blocks['pcr_create_directory'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_create_directory",
      "message0": "Create directory %1",
      "args0": [
        { "type": "input_value", "name": "PATH", "check": ["String", "RESLOC"] }
      ],
      "previousStatement": null,
      "nextStatement": null,
      "colour": 270,
      "tooltip": "Create a directory (and parent directories if needed)"
    });
  }
};

// ─── Python Generator ───
Blockly.Python['pcr_create_directory'] = function(block) {
  var path = 'resolve_path(' + (Blockly.Python.valueToCode(block, 'PATH', Blockly.Python.ORDER_NONE) || "''") + ')';
  return 'os.makedirs(' + path + ', exist_ok=True)\n';
};
