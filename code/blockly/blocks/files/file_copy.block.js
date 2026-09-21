// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_file_copy                            ║
// ║ Category: file_manager                        ║
// ║ Source: MCreator File Manager plugin           ║
// ║ Desc: Copy file to new location               ║
// ╚══════════════════════════════════════════════╝

// ─── Definition ───
Blockly.Blocks['pcr_file_copy'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_file_copy",
      "message0": "Copy file %1 to %2",
      "args0": [
        { "type": "input_value", "name": "SOURCE", "check": ["String", "RESLOC"] },
        { "type": "input_value", "name": "DEST", "check": ["String", "RESLOC"] }
      ],
      "inputsInline": true,
      "previousStatement": null,
      "nextStatement": null,
      "colour": 270,
      "tooltip": "Copy a file to a new location"
    });
  }
};

// ─── Python Generator ───
Blockly.Python['pcr_file_copy'] = function(block) {
  var src = 'resolve_path(' + (Blockly.Python.valueToCode(block, 'SOURCE', Blockly.Python.ORDER_NONE) || "''") + ')';
  var dst = 'resolve_path(' + (Blockly.Python.valueToCode(block, 'DEST', Blockly.Python.ORDER_NONE) || "''") + ')';
  var code = 'import shutil\n';
  code += 'try:\n';
  code += '    shutil.copy2(' + src + ', ' + dst + ')\n';
  code += 'except (OSError, shutil.Error) as e:\n';
  code += '    print(f"Error copying file: {e}")\n';
  return code;
};
