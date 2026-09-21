// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_file_read_text                       ║
// ║ Category: file_manager                        ║
// ║ Source: Extra (not in MCreator plugin)        ║
// ║ Desc: Read entire file as text                ║
// ╚══════════════════════════════════════════════╝

// ─── Definition ───
Blockly.Blocks['pcr_file_read_text'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_file_read_text",
      "message0": "Read text from %1",
      "args0": [
        { "type": "input_value", "name": "PATH", "check": ["String", "RESLOC"] }
      ],
      "output": "String",
      "colour": 160,
      "tooltip": "Read the entire contents of a file as text"
    });
  }
};

// ─── Python Generator ───
Blockly.Python['pcr_file_read_text'] = function(block) {
  var path = 'resolve_path(' + (Blockly.Python.valueToCode(block, 'PATH', Blockly.Python.ORDER_ATOMIC) || "''") + ')';
  var code = 'open(' + path + ', "r", encoding="utf-8").read()';
  return [code, Blockly.Python.ORDER_FUNCTION_CALL];
};
