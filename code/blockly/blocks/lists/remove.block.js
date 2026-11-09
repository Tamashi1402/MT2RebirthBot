// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_list_remove                          ║
// ║ Category: base/lists                          ║
// ║ Desc: Remove an item from a list at an index   ║
// ║ Colour: 260 (list purple)                     ║
// ╚══════════════════════════════════════════════╝

// ─── Block Definition ───
Blockly.Blocks['pcr_list_remove'] = {
  init: function() {
    this.appendValueInput("LIST")
      .setCheck(null)
      .appendField("remove item at");
    this.appendValueInput("INDEX")
      .setCheck("Number")
      .appendField("from list");
    this.setInputsInline(true);
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour(260);
    this.setTooltip("Remove an item from a list at the given index (like Python's del list[i] or list.pop(i)).");
  }
};

// ─── Python Generator ───
Blockly.Python['pcr_list_remove'] = function(block) {
  var list = Blockly.Python.valueToCode(block, 'LIST', Blockly.Python.ORDER_MEMBER) || '[]';
  var index = Blockly.Python.valueToCode(block, 'INDEX', Blockly.Python.ORDER_NONE) || '0';
  return list + '.pop(int(' + index + '))\n';
};
