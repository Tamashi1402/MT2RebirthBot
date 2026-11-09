// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_file_append_line                      ║
// ║ Category: file_manager                        ║
// ║ Source: Extra (not in MCreator plugin)        ║
// ║ Desc: Append a line to file                  ║
// ╚══════════════════════════════════════════════╝

// ─── Definition ───
Blockly.Blocks['pcr_file_append_line'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_file_append_line",
      "message0": "Append line %1 to file %2",
      "args0": [
        { "type": "input_value", "name": "LINE", "check": "String" },
        { "type": "input_value", "name": "PATH", "check": ["String", "RESLOC"] }
      ],
      "inputsInline": true,
      "previousStatement": null,
      "nextStatement": null,
      "colour": 270,
      "tooltip": "Append a line of text to the end of a file"
    });
  }
};

// ─── Python Generator ───
Blockly.Python['pcr_file_append_line'] = function(block) {
  var line = Blockly.Python.valueToCode(block, 'LINE', Blockly.Python.ORDER_NONE) || "''";
  var path = 'resolve_path(' + (Blockly.Python.valueToCode(block, 'PATH', Blockly.Python.ORDER_NONE) || "''") + ')';
  var code = 'with open(' + path + ", 'a') as f:\n";
  code += '    f.write(str(' + line + ") + '\\n')\n";
  return code;
};
