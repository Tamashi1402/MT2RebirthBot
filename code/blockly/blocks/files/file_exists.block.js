// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_file_exists                          ║
// ║ Category: file_manager                        ║
// ║ Source: MCreator File Manager plugin           ║
// ║ Desc: Check if file/path exists              ║
// ╚══════════════════════════════════════════════╝

// ─── Definition ───
Blockly.Blocks['pcr_file_exists'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_file_exists",
      "message0": "Exists %1",
      "args0": [
        { "type": "input_value", "name": "PATH", "check": ["String", "RESLOC"] }
      ],
      "output": "Boolean",
      "colour": 210,
      "tooltip": "Check if a file or directory exists"
    });
  }
};

// ─── Python Generator ───
Blockly.Python['pcr_file_exists'] = function(block) {
  var path = 'resolve_path(' + (Blockly.Python.valueToCode(block, 'PATH', Blockly.Python.ORDER_ATOMIC) || "''") + ')';
  return ['os.path.exists(' + path + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};
