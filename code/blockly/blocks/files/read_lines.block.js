// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_read_lines                            ║
// ║ Category: file_manager                        ║
// ║ Source: Extra                                  ║
// ║ Desc: Read file lines into list               ║
// ╚══════════════════════════════════════════════╝

// ─── Definition ───
Blockly.Blocks['pcr_read_lines'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_read_lines",
      "message0": "Read lines from %1",
      "args0": [
        { "type": "input_value", "name": "PATH", "check": ["String", "RESLOC"] }
      ],
      "output": "Array",
      "colour": 260,
      "tooltip": "Read a file and return a list of lines"
    });
  }
};

// ─── Python Generator ───
Blockly.Python['pcr_read_lines'] = function(block) {
  var path = 'resolve_path(' + (Blockly.Python.valueToCode(block, 'PATH', Blockly.Python.ORDER_ATOMIC) || "''") + ')';
  var code = '(lambda p: open(p, "r").readlines())(' + path + ')';
  return [code, Blockly.Python.ORDER_FUNCTION_CALL];
};
