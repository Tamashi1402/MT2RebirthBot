// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_time_parts                            ║
// ║ Category: time                                ║
// ║ Library: datetime                              ║
// ║ Desc: Extract date/time parts                  ║
// ╚══════════════════════════════════════════════╝

Blockly.Blocks['pcr_time_parts'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_time_parts",
      "message0": "%1 of %2",
      "args0": [
        {
          "type": "field_dropdown",
          "name": "PART",
          "options": [
            ["year", "year"], ["month", "month"], ["day", "day"],
            ["hour", "hour"], ["minute", "minute"], ["second", "second"],
            ["weekday", "weekday"], ["day of year", "timetuple().tm_yday"]
          ]
        },
        { "type": "input_value", "name": "DATETIME" }
      ],
      "inputsInline": true, "output": "Number", "colour": 230,
      "tooltip": "Extract a specific part (year, month, etc.) from a datetime"
    });
  }
};

Blockly.Python['pcr_time_parts'] = function(block) {
  var part = block.getFieldValue('PART');
  var dt = Blockly.Python.valueToCode(block, 'DATETIME', Blockly.Python.ORDER_ATOMIC) || 'datetime.datetime.now()';
  if (part === 'weekday') {
    return [dt + '.weekday()', Blockly.Python.ORDER_FUNCTION_CALL];
  }
  return [dt + '.' + part, Blockly.Python.ORDER_MEMBER];
};
