// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_file_create                          ║
// ║ Category: file_manager                        ║
// ║ Source: MCreator File Manager plugin           ║
// ║ Desc: Create a new file (and parent dirs)     ║
// ╚══════════════════════════════════════════════╝

// ─── Definition ───
Blockly.Blocks['pcr_file_create'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_file_create",
      "message0": "Create file at %1",
      "args0": [
        { "type": "input_value", "name": "PATH", "check": ["String", "RESLOC"] }
      ],
      "previousStatement": null,
      "nextStatement": null,
      "colour": 270,
      "tooltip": "Create a new empty file, creating parent directories if needed"
    });
  }
};

// ─── Python Generator ───
Blockly.Python['pcr_file_create'] = function(block) {
  var path = 'resolve_path(' + (Blockly.Python.valueToCode(block, 'PATH', Blockly.Python.ORDER_NONE) || "''") + ')';
  var code = 'import os\n';
  code += 'try:\n';
  code += '    _dir = os.path.dirname(' + path + ')\n';
  code += '    if _dir:\n';
  code += '        os.makedirs(_dir, exist_ok=True)\n';
  code += '    open(' + path + ", 'w').close()\n";
  code += 'except OSError as e:\n';
  code += '    print(f"Error creating file: {e}")\n';
  return code;
};
