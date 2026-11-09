// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_run_command_output                   ║
// ║ Category: system                              ║
// ║ Library: subprocess                            ║
// ║ Desc: Run command and capture output           ║
// ╚══════════════════════════════════════════════╝

Blockly.Blocks['pcr_run_command_output'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_run_command_output", "message0": "Output of command %1",
      "args0": [{ "type": "input_value", "name": "COMMAND", "check": "String" }],
      "output": "String", "colour": 160,
      "tooltip": "Run a command and return its stdout output as a string"
    });
  }
};

Blockly.Python['pcr_run_command_output'] = function(block) {
  var cmd = Blockly.Python.valueToCode(block, 'COMMAND', Blockly.Python.ORDER_NONE) || "''";
  var code = 'subprocess.run(' + cmd + ', shell=True, capture_output=True, text=True).stdout';
  return [code, Blockly.Python.ORDER_MEMBER];
};
