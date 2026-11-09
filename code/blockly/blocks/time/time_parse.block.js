// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_time_parse                            ║
// ║ Category: time                                ║
// ║ Library: datetime                              ║
// ║ Desc: Parse string to datetime                ║
// ╚══════════════════════════════════════════════╝

Blockly.Blocks['pcr_time_parse'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_time_parse",
      "message0": "Parse %1 with format %2",
      "args0": [
        { "type": "input_value", "name": "TEXT", "check": "String" },
        { "type": "input_value", "name": "FORMAT", "check": "String" }
      ],
      "inputsInline": true, "output": null, "colour": 90,
      "tooltip": "Parse a date string into a datetime object using a format"
    });
  }
};

Blockly.Python['pcr_time_parse'] = function(block) {
  var text = Blockly.Python.valueToCode(block, 'TEXT', Blockly.Python.ORDER_NONE) || "''";
  var fmt = Blockly.Python.valueToCode(block, 'FORMAT', Blockly.Python.ORDER_NONE) || "'%Y-%m-%d'";
  return ['datetime.datetime.strptime(' + text + ', ' + fmt + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};
