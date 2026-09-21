// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_path_join                             ║
// ║ Category: file_manager                        ║
// ║ Source: MCreator File Manager (path_separator)  ║
// ║ Desc: Join two path segments                   ║
// ╚══════════════════════════════════════════════╝

// ─── Definition ───
Blockly.Blocks['pcr_path_join'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_path_join",
      "message0": "Join paths %1 and %2",
      "args0": [
        { "type": "input_value", "name": "PATH_A", "check": "String" },
        { "type": "input_value", "name": "PATH_B", "check": "String" }
      ],
      "inputsInline": true,
      "output": "String",
      "colour": 160,
      "tooltip": "Join two path segments into one path"
    });
  }
};

// ─── Python Generator ───
Blockly.Python['pcr_path_join'] = function(block) {
  var a = Blockly.Python.valueToCode(block, 'PATH_A', Blockly.Python.ORDER_NONE) || "''";
  var b = Blockly.Python.valueToCode(block, 'PATH_B', Blockly.Python.ORDER_NONE) || "''";
  return ['macroforge.engine.functions.call("macroforge.engine.path.join", ' + a + ', ' + b + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};
