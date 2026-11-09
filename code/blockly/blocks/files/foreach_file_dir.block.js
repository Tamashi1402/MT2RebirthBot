// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_foreach_file_dir                      ║
// ║ Category: file_manager                        ║
// ║ Source: MCreator File Manager (directory_foreach)║
// ║ Desc: Iterate files in a directory            ║
// ╚══════════════════════════════════════════════╝

// ─── Definition ───
Blockly.Blocks['pcr_foreach_file_dir'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_foreach_file_dir",
      "message0": "For each file in directory %1 as %2 do %3",
      "args0": [
        { "type": "input_value", "name": "DIR", "check": ["String", "RESLOC"] },
        { "type": "field_variable", "name": "FILE_VAR", "variable": "file" },
        { "type": "input_statement", "name": "DO" }
      ],
      "previousStatement": null,
      "nextStatement": null,
      "colour": 270,
      "tooltip": "Loop over each file in a directory"
    });
  }
};

// ─── Python Generator ───
Blockly.Python['pcr_foreach_file_dir'] = function(block) {
  var dir = 'resolve_path(' + (Blockly.Python.valueToCode(block, 'DIR', Blockly.Python.ORDER_NONE) || "'.'") + ')';
  var fileVar = Blockly.Python.variableDB_.getName(block.getFieldValue('FILE_VAR'), Blockly.VARIABLE_CATEGORY_NAME);
  var branch = Blockly.Python.statementToCode(block, 'DO') || '    pass\n';

  var IND = Blockly.Python.INDENT || '    ';
  var code = 'for name in os.listdir(' + dir + '):\n';
  code += IND + 'if stopped():\n';
  code += IND + IND + 'break\n';
  code += IND + fileVar + ' = os.path.join(' + dir + ', name)\n';
  code += branch;
  return code;
};
