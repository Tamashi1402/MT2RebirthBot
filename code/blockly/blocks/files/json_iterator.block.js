// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_json_iterator                         ║
// ║ Category: file_manager                        ║
// ║ Source: MCreator File Manager (json_iterator)   ║
// ║ Desc: Iterate over JSON object keys/values     ║
// ╚══════════════════════════════════════════════╝

// ─── Definition ───
Blockly.Blocks['pcr_json_iterator'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_json_iterator",
      "message0": "For each key %1 value %2 in %3 do %4",
      "args0": [
        { "type": "field_variable", "name": "KEY_VAR", "variable": "key" },
        { "type": "field_variable", "name": "VALUE_VAR", "variable": "value" },
        { "type": "input_value", "name": "DATA" },
        { "type": "input_statement", "name": "DO" }
      ],
      "previousStatement": null,
      "nextStatement": null,
      "colour": 270,
      "tooltip": "Iterate over each key-value pair in a JSON object / dict"
    });
  }
};

// ─── Python Generator ───
Blockly.Python['pcr_json_iterator'] = function(block) {
  var keyVar = Blockly.Python.variableDB_.getName(block.getFieldValue('KEY_VAR'), Blockly.VARIABLE_CATEGORY_NAME);
  var valVar = Blockly.Python.variableDB_.getName(block.getFieldValue('VALUE_VAR'), Blockly.VARIABLE_CATEGORY_NAME);
  var data = Blockly.Python.valueToCode(block, 'DATA', Blockly.Python.ORDER_ATOMIC) || '{}';
  var branch = Blockly.Python.statementToCode(block, 'DO') || '    pass\n';

  return 'for ' + keyVar + ', ' + valVar + ' in ' + data + '.items():\n' + branch;
};
