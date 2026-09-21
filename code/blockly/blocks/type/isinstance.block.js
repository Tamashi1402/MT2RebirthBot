// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_isinstance                           ║
// ║ Category: base/type                           ║
// ║ Built-in: No (custom)                          ║
// ║ Desc: Check if value is of a type            ║
// ╚══════════════════════════════════════════════╝

// ─── Definition ───
Blockly.Blocks['pcr_isinstance'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_isinstance",
      "message0": "%1 is %2",
      "args0": [
        { "type": "input_value", "name": "VALUE" },
        {
          "type": "field_dropdown",
          "name": "TYPE",
          "options": [
            ["int", "int"],
            ["float", "float"],
            ["str", "str"],
            ["bool", "bool"],
            ["list", "list"],
            ["dict", "dict"],
            ["None", "None"]
          ]
        }
      ],
      "output": "Boolean",
      "colour": 210,
      "tooltip": "Check if a value is of a specific type"
    });
  }
};

// ─── Python Generator ───
Blockly.Python['pcr_isinstance'] = function(block) {
  var value = Blockly.Python.valueToCode(block, 'VALUE', Blockly.Python.ORDER_ATOMIC) || 'None';
  var type = block.getFieldValue('TYPE');

  if (type === 'None') {
    return [value + ' is None', Blockly.Python.ORDER_RELATIONAL];
  }
  return ['isinstance(' + value + ', ' + type + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};
