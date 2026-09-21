// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_path_desktop                          ║
// ║ Category: file_manager                        ║
// ║ Desc: User Desktop folder (string colour)     ║
// ╚══════════════════════════════════════════════╝

Blockly.Blocks['pcr_path_desktop'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_path_desktop",
      "message0": "desktop location",
      "output": "String",
      "colour": 160,
      "tooltip": "User Desktop folder."
    });
  }
};

Blockly.Python['pcr_path_desktop'] = function() {
  return ['macroforge.engine.functions.call("macroforge.engine.path.desktop")', Blockly.Python.ORDER_FUNCTION_CALL];
};
