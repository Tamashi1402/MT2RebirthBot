// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_is_file                              ║
// ║ Category: file_manager                        ║
// ║ Source: MCreator File Manager plugin           ║
// ║ Desc: Check if path is a file                 ║
// ╚══════════════════════════════════════════════╝

// ─── Definition ───
Blockly.Blocks['pcr_is_file'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_is_file",
      "message0": "Is file %1",
      "args0": [
        { "type": "input_value", "name": "PATH", "check": ["String", "RESLOC"] }
      ],
      "output": "Boolean",
      "colour": 210,
      "tooltip": "Check if a path is a file"
    });
  }
};

// ─── Python Generator ───
Blockly.Python['pcr_is_file'] = function(block) {
  var path = 'resolve_path(' + (Blockly.Python.valueToCode(block, 'PATH', Blockly.Python.ORDER_ATOMIC) || "''") + ')';
  return ['os.path.isfile(' + path + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};
