// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_get_file_dir                          ║
// ║ Category: file_manager                        ║
// ║ Source: MCreator File Manager plugin (parent)  ║
// ║ Desc: Get directory from path                ║
// ╚══════════════════════════════════════════════╝

// ─── Definition ───
Blockly.Blocks['pcr_get_file_dir'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_get_file_dir",
      "message0": "Directory of %1",
      "args0": [
        { "type": "input_value", "name": "PATH", "check": ["String", "RESLOC"] }
      ],
      "output": "String",
      "colour": 160,
      "tooltip": "Get the directory path from a full file path"
    });
  }
};

// ─── Python Generator ───
Blockly.Python['pcr_get_file_dir'] = function(block) {
  var path = 'resolve_path(' + (Blockly.Python.valueToCode(block, 'PATH', Blockly.Python.ORDER_ATOMIC) || "''") + ')';
  return ['os.path.dirname(' + path + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};
