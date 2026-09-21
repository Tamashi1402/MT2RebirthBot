// Block: lists_join — join list elements into a string with separator
// This block is NOT in our Blockly build, so we define it ourselves.

Blockly.Blocks['lists_join'] = {
  init: function() {
    var SEPARATOR = [
      ["comma", ","],
      ["space", " "],
      ["newline", "\n"],
      ["none", ""]
    ];
    this.jsonInit({
      "type": "lists_join",
      "message0": "join %1 with %2",
      "args0": [
        { "type": "input_value", "name": "LIST", "check": "Array" },
        { "type": "field_dropdown", "name": "SEPARATOR", "options": SEPARATOR }
      ],
      "inputsInline": true,
      "output": "String", "colour": 160,
      "tooltip": "Join all items in a list into a single text string, separated by the chosen delimiter"
    });
  }
};

Blockly.Python['lists_join'] = function(block) {
  var list = Blockly.Python.valueToCode(block, 'LIST', Blockly.Python.ORDER_NONE) || '[]';
  var delim = block.getFieldValue('SEPARATOR');
  var delimCode;
  switch (delim) {
    case ',':      delimCode = "','"; break;
    case ' ':      delimCode = "' '"; break;
    case '\n':     delimCode = "'\\n'"; break;
    default:       delimCode = "''"; break;
  }
  return [delimCode + '.join(str(x) for x in ' + list + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};
