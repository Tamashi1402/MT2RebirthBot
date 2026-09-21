// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_file_copy_to_dir                      ║
// ║ Category: file_manager                        ║
// ║ Source: Extra                                  ║
// ║ Desc: Copy file into a directory              ║
// ╚══════════════════════════════════════════════╝

// ─── Definition ───
Blockly.Blocks['pcr_file_copy_to_dir'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_file_copy_to_dir",
      "message0": "Copy file %1 into directory %2",
      "args0": [
        { "type": "input_value", "name": "SOURCE", "check": ["String", "RESLOC"] },
        { "type": "input_value", "name": "DIR", "check": ["String", "RESLOC"] }
      ],
      "inputsInline": true,
      "previousStatement": null,
      "nextStatement": null,
      "colour": 270,
      "tooltip": "Copy a file into a target directory (keeping the filename)"
    });
  }
};

// ─── Python Generator ───
Blockly.Python['pcr_file_copy_to_dir'] = function(block) {
  var src = 'resolve_path(' + (Blockly.Python.valueToCode(block, 'SOURCE', Blockly.Python.ORDER_NONE) || "''") + ')';
  var dir = 'resolve_path(' + (Blockly.Python.valueToCode(block, 'DIR', Blockly.Python.ORDER_NONE) || "''") + ')';
  var code = 'import shutil\n';
  code += 'shutil.copy2(' + src + ', ' + dir + ')\n';
  return code;
};
