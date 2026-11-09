// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_file_size                             ║
// ║ Category: file_manager                        ║
// ║ Source: Extra                                  ║
// ║ Desc: Get file size in bytes                 ║
// ╚══════════════════════════════════════════════╝

// ─── Definition ───
Blockly.Blocks['pcr_file_size'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_file_size",
      "message0": "Size of %1 in bytes",
      "args0": [
        { "type": "input_value", "name": "PATH", "check": ["String", "RESLOC"] }
      ],
      "output": "Number",
      "colour": 230,
      "tooltip": "Get the size of a file in bytes"
    });
  }
};

// ─── Python Generator ───
Blockly.Python['pcr_file_size'] = function(block) {
  var path = 'resolve_path(' + (Blockly.Python.valueToCode(block, 'PATH', Blockly.Python.ORDER_ATOMIC) || "''") + ')';
  return ['os.path.getsize(' + path + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};
