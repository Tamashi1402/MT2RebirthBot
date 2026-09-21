// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_key                                ║
// ║ Category: input / Data                        ║
// ║ Desc: Keyboard key picker (dropdown stub)     ║
// ╚══════════════════════════════════════════════╝
// @mf-category: Input/Data

Blockly.Blocks['pcr_key'] = {
  init: function () {
    var opts = (typeof MF_KEYS !== 'undefined' && MF_KEYS.dropdown)
      ? MF_KEYS.dropdown('keys')
      : [['Space', 'space']];
    this.appendDummyInput().appendField(new Blockly.FieldDropdown(opts), 'KEY');
    this.setOutput(true, ['Key', 'String']);
    this.setColour(40);
    this.setTooltip('A keyboard key.');
  }
};

Blockly.Python['pcr_key'] = function (block) {
  return [JSON.stringify(block.getFieldValue('KEY') || 'space'), Blockly.Python.ORDER_ATOMIC];
};
