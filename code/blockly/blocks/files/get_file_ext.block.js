// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_get_file_ext                          ║
// ║ Category: file_manager                        ║
// ║ Source: Extra                                  ║
// ║ Desc: Get file extension                     ║
// ╚══════════════════════════════════════════════╝

// ─── Definition ───
Blockly.Blocks['pcr_get_file_ext'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_get_file_ext",
      "message0": "Extension of %1",
      "args0": [
        { "type": "input_value", "name": "PATH", "check": ["String", "RESLOC"] }
      ],
      "output": "String",
      "colour": 160,
      "tooltip": "Get the file extension (e.g. .txt) from a path"
    });
  }
};

// ─── Python Generator ───
Blockly.Python['pcr_get_file_ext'] = function(block) {
  var path = 'resolve_path(' + (Blockly.Python.valueToCode(block, 'PATH', Blockly.Python.ORDER_ATOMIC) || "''") + ')';
  return ['os.path.splitext(' + path + ')[1]', Blockly.Python.ORDER_MEMBER];
};
