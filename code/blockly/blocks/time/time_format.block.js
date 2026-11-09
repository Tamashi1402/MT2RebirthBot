// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_time_format                           ║
// ║ Category: time                                ║
// ║ Library: datetime                              ║
// ║ Desc: Format datetime to string               ║
// ╚══════════════════════════════════════════════╝

Blockly.Blocks['pcr_time_format'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_time_format",
      "message0": "Format %1 as %2",
      "args0": [
        { "type": "input_value", "name": "DATETIME" },
        { "type": "input_value", "name": "FORMAT", "check": "String" }
      ],
      "inputsInline": true, "output": "String", "colour": 160,
      "tooltip": "Format a datetime object as a string (e.g. %Y-%m-%d %H:%M:%S)"
    });
  }
};

Blockly.Python['pcr_time_format'] = function(block) {
  var dt = Blockly.Python.valueToCode(block, 'DATETIME', Blockly.Python.ORDER_ATOMIC) || 'datetime.datetime.now()';
  var fmt = Blockly.Python.valueToCode(block, 'FORMAT', Blockly.Python.ORDER_NONE) || "'%Y-%m-%d %H:%M:%S'";
  return [dt + '.strftime(' + fmt + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};
