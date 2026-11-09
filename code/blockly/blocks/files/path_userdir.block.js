// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_path_userdir                          ║
// ║ Category: file_manager                        ║
// ║ Source: MCreator File Manager                   ║
// ║ Desc: Get user's home directory path          ║
// ╚══════════════════════════════════════════════╝

// ─── Definition ───
Blockly.Blocks['pcr_path_userdir'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_path_userdir",
      "message0": "User home directory",
      "output": "String",
      "colour": 160,
      "tooltip": "Get the path to the user's home directory"
    });
  }
};

// ─── Python Generator ───
Blockly.Python['pcr_path_userdir'] = function(block) {
  return ['os.path.expanduser("~")', Blockly.Python.ORDER_FUNCTION_CALL];
};
