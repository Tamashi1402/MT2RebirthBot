// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_path_tempdir                          ║
// ║ Category: file_manager                        ║
// ║ Source: MCreator File Manager (get_temp_dir)   ║
// ║ Desc: Get system temp directory path         ║
// ╚══════════════════════════════════════════════╝

// ─── Definition ───
Blockly.Blocks['pcr_path_tempdir'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_path_tempdir",
      "message0": "Temp directory",
      "output": "String",
      "colour": 160,
      "tooltip": "Get the path to the system's temporary directory"
    });
  }
};

// ─── Python Generator ───
Blockly.Python['pcr_path_tempdir'] = function(block) {
  return ['tempfile.gettempdir()', Blockly.Python.ORDER_FUNCTION_CALL];
};
