// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_env_get                              ║
// ║ Category: system                              ║
// ║ Library: os                                    ║
// ║ Desc: Get environment variable                ║
// ╚══════════════════════════════════════════════╝

Blockly.Blocks['pcr_env_get'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_env_get", "message0": "Get env var %1",
      "args0": [{ "type": "input_value", "name": "NAME", "check": "String" }],
      "output": "String", "colour": 160,
      "tooltip": "Get the value of an environment variable"
    });
  }
};

Blockly.Python['pcr_env_get'] = function(block) {
  var name = Blockly.Python.valueToCode(block, 'NAME', Blockly.Python.ORDER_NONE) || "''";
  return ['os.environ.get(' + name + ", '')", Blockly.Python.ORDER_FUNCTION_CALL];
};
