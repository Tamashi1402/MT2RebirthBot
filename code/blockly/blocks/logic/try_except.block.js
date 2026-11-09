// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_try_except                          ║
// ║ Category: base/logic                          ║
// ║ Built-in: No (custom)                          ║
// ║ Desc: Try / Except error handling             ║
// ╚══════════════════════════════════════════════╝

// ─── Definition ───
Blockly.Blocks['pcr_try_except'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_try_except",
      "message0": "Try %1 Except as %2 %3",
      "args0": [
        { "type": "input_statement", "name": "TRY" },
        { "type": "field_variable", "name": "ERR_VAR", "variable": "error" },
        { "type": "input_statement", "name": "CATCH" }
      ],
      "previousStatement": null,
      "nextStatement": null,
      "colour": 210,
      "tooltip": "Try code and catch any errors"
    });
  }
};

// ─── Python Generator ───
Blockly.Python['pcr_try_except'] = function(block) {
  var errVar = Blockly.Python.variableDB_.getName(block.getFieldValue('ERR_VAR'), Blockly.VARIABLE_CATEGORY_NAME);
  var tryCode = Blockly.Python.statementToCode(block, 'TRY') || '    pass\n';
  var catchCode = Blockly.Python.statementToCode(block, 'CATCH') || '    pass\n';

  var code = 'try:\n' + tryCode;
  code += 'except Exception as ' + errVar + ':\n';
  code += catchCode;
  return code;
};
