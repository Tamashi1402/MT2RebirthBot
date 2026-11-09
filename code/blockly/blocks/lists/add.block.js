// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_list_add                             ║
// ║ Category: base/lists                          ║
// ║ Desc: Add (append) an item to the end of a list ║
// ║ Colour: 260 (list purple)                     ║
// ╚══════════════════════════════════════════════╝

// ─── Block Definition ───
Blockly.Blocks['pcr_list_add'] = {
  init: function() {
    this.appendValueInput("LIST")
      .setCheck(null)
      .appendField("add");
    this.appendValueInput("ITEM")
      .setCheck(null)
      .appendField("to list");
    this.setInputsInline(true);
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour(260);
    this.setTooltip("Append an item to the end of a list (like Python's list.append()).");
  }
};

// ─── Python Generator ───
Blockly.Python['pcr_list_add'] = function(block) {
  var list = Blockly.Python.valueToCode(block, 'LIST', Blockly.Python.ORDER_MEMBER) || '[]';
  var item = Blockly.Python.valueToCode(block, 'ITEM', Blockly.Python.ORDER_NONE) || 'None';
  return list + '.append(' + item + ')\n';
};
