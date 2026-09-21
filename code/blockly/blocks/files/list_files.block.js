// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_list_files                            ║
// ║ Category: file_manager                        ║
// ║ Source: Extra                                  ║
// ║ Desc: List files in a directory              ║
// ╚══════════════════════════════════════════════╝

// ─── Definition ───
Blockly.Blocks['pcr_list_files'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_list_files",
      "message0": "List files in %1",
      "args0": [
        { "type": "input_value", "name": "DIR", "check": ["String", "RESLOC"] }
      ],
      "output": "Array",
      "colour": 260,
      "tooltip": "Get a list of file names in a directory"
    });
  }
};

// ─── Python Generator ───
Blockly.Python['pcr_list_files'] = function(block) {
  var dir = 'resolve_path(' + (Blockly.Python.valueToCode(block, 'DIR', Blockly.Python.ORDER_ATOMIC) || "'.'") + ')';
  return ['os.listdir(' + dir + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};
