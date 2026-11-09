// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_run_command                          ║
// ║ Category: system                              ║
// ║ Library: subprocess                            ║
// ║ Desc: Run a system command                     ║
// ╚══════════════════════════════════════════════╝

Blockly.Blocks['pcr_run_command'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_run_command", "message0": "Run command %1",
      "args0": [{ "type": "input_value", "name": "COMMAND", "check": "String" }],
      "previousStatement": null, "nextStatement": null, "colour": 210,
      "tooltip": "Run a shell/system command"
    });
  }
};

Blockly.Python['pcr_run_command'] = function(block) {
  var cmd = Blockly.Python.valueToCode(block, 'COMMAND', Blockly.Python.ORDER_NONE) || "''";
  return 'subprocess.run(' + cmd + ', shell=True)\n';
};
