// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_mouse                              ║
// ║ Category: input / Data                        ║
// ║ Desc: Mouse button picker (dropdown stub)     ║
// ╚══════════════════════════════════════════════╝
// @mf-category: Input/Data

Blockly.Blocks['pcr_mouse'] = {
  init: function () {
    var opts = (typeof MF_KEYS !== 'undefined' && MF_KEYS.dropdown)
      ? MF_KEYS.dropdown('mouse')
      : [['Left click', 'left']];
    this.appendDummyInput().appendField(new Blockly.FieldDropdown(opts), 'BUTTON');
    this.setOutput(true, ['Mouse', 'Key', 'String']);
    this.setColour(40);
    this.setTooltip('A mouse button.');
  }
};

Blockly.Python['pcr_mouse'] = function (block) {
  return [JSON.stringify(block.getFieldValue('BUTTON') || 'left'), Blockly.Python.ORDER_ATOMIC];
};
