// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_get_file_name                         ║
// ║ Category: file_manager                        ║
// ║ Source: MCreator File Manager plugin           ║
// ║ Desc: Get filename from path                ║
// ╚══════════════════════════════════════════════╝

// ─── Definition ───
Blockly.Blocks['pcr_get_file_name'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_get_file_name",
      "message0": "File name of %1",
      "args0": [
        { "type": "input_value", "name": "PATH", "check": ["String", "RESLOC"] }
      ],
      "output": "String",
      "colour": 160,
      "tooltip": "Get the file name (with extension) from a full path"
    });
  }
};

// ─── Python Generator ───
Blockly.Python['pcr_get_file_name'] = function(block) {
  var path = 'resolve_path(' + (Blockly.Python.valueToCode(block, 'PATH', Blockly.Python.ORDER_ATOMIC) || "''") + ')';
  return ['os.path.basename(' + path + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};
