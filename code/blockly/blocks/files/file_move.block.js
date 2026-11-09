// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_file_move                            ║
// ║ Category: file_manager                        ║
// ║ Source: MCreator File Manager plugin           ║
// ║ Desc: Move / rename a file                    ║
// ╚══════════════════════════════════════════════╝

// ─── Definition ───
Blockly.Blocks['pcr_file_move'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_file_move",
      "message0": "Move file %1 to %2",
      "args0": [
        { "type": "input_value", "name": "SOURCE", "check": ["String", "RESLOC"] },
        { "type": "input_value", "name": "DEST", "check": ["String", "RESLOC"] }
      ],
      "inputsInline": true,
      "previousStatement": null,
      "nextStatement": null,
      "colour": 270,
      "tooltip": "Move or rename a file"
    });
  }
};

// ─── Python Generator ───
Blockly.Python['pcr_file_move'] = function(block) {
  var src = 'resolve_path(' + (Blockly.Python.valueToCode(block, 'SOURCE', Blockly.Python.ORDER_NONE) || "''") + ')';
  var dst = 'resolve_path(' + (Blockly.Python.valueToCode(block, 'DEST', Blockly.Python.ORDER_NONE) || "''") + ')';
  var code = 'import shutil\n';
  code += 'shutil.move(' + src + ', ' + dst + ')\n';
  return code;
};
