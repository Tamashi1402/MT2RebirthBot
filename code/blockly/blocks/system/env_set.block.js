// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_env_set                              ║
// ║ Category: system                              ║
// ║ Library: os                                    ║
// ║ Desc: Set environment variable               ║
// ╚══════════════════════════════════════════════╝

Blockly.Blocks['pcr_env_set'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_env_set", "message0": "Set env var %1 to %2",
      "args0": [
        { "type": "input_value", "name": "NAME", "check": "String" },
        { "type": "input_value", "name": "VALUE", "check": "String" }
      ],
      "inputsInline": true, "previousStatement": null, "nextStatement": null, "colour": 210,
      "tooltip": "Set an environment variable for this process"
    });
  }
};

Blockly.Python['pcr_env_set'] = function(block) {
  var name = Blockly.Python.valueToCode(block, 'NAME', Blockly.Python.ORDER_NONE) || "''";
  var value = Blockly.Python.valueToCode(block, 'VALUE', Blockly.Python.ORDER_NONE) || "''";
  return 'os.environ[' + name + '] = ' + value + '\n';
};
