// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_path_separator                        ║
// ║ Category: file_manager                        ║
// ║ Source: MCreator File Manager (path_separator) ║
// ║ Desc: Get OS path separator                   ║
// ╚══════════════════════════════════════════════╝

// ─── Definition ───
Blockly.Blocks['pcr_path_separator'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_path_separator",
      "message0": "Path separator",
      "output": "String",
      "colour": 160,
      "tooltip": "Get the OS-specific path separator (/ or \\)"
    });
  }
};

// ─── Python Generator ───
Blockly.Python['pcr_path_separator'] = function(block) {
  return ['os.sep', Blockly.Python.ORDER_ATOMIC];
};
