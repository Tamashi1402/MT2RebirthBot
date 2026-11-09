// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_is_directory                          ║
// ║ Category: file_manager                        ║
// ║ Source: MCreator File Manager plugin           ║
// ║ Desc: Check if path is a directory          ║
// ╚══════════════════════════════════════════════╝

// ─── Definition ───
Blockly.Blocks['pcr_is_directory'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_is_directory",
      "message0": "Is directory %1",
      "args0": [
        { "type": "input_value", "name": "PATH", "check": ["String", "RESLOC"] }
      ],
      "output": "Boolean",
      "colour": 210,
      "tooltip": "Check if a path is a directory"
    });
  }
};

// ─── Python Generator ───
Blockly.Python['pcr_is_directory'] = function(block) {
  var path = 'resolve_path(' + (Blockly.Python.valueToCode(block, 'PATH', Blockly.Python.ORDER_ATOMIC) || "''") + ')';
  return ['os.path.isdir(' + path + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};
