// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_print                                ║
// ║ Category: base/text                           ║
// ║ Built-in: No (custom)                          ║
// ║ Desc: Print to console                        ║
// ╚══════════════════════════════════════════════╝

// ─── Definition ───
Blockly.Blocks['pcr_print'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_print",
      "message0": "Print %1",
      "args0": [
        { "type": "input_value", "name": "TEXT" }
      ],
      "previousStatement": null,
      "nextStatement": null,
      "colour": 160,
      "tooltip": "Print to the Console (Dashboard \u2192 Console)"
    });
  }
};

// ─── Python Generator ───
Blockly.Python['pcr_print'] = function(block) {
  var text = Blockly.Python.valueToCode(block, 'TEXT', Blockly.Python.ORDER_NONE) || "''";
  return 'print(' + text + ')\n';
};
