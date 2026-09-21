// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_mouse_scroll                       ║
// ║ Category: input                               ║
// ║ Library: mouse                                ║
// ║ Desc: Scroll mouse wheel                      ║
// ╚══════════════════════════════════════════════╝

Blockly.Blocks['pcr_mouse_scroll'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_mouse_scroll",
      "message0": "Scroll %1 %2",
      "args0": [
        { "type": "input_value", "name": "DELTA", "check": "Number" },
        { "type": "field_dropdown", "name": "DIR", "options": [["up", "up"], ["down", "down"]] }
      ],
      "previousStatement": null,
      "nextStatement": null,
      "colour": 40,
      "tooltip": "Scroll the mouse wheel by this many notches, up or down"
    });
  }
};

Blockly.Python['pcr_mouse_scroll'] = function(block) {
  var delta = Blockly.Python.valueToCode(block, 'DELTA', Blockly.Python.ORDER_NONE) || '1';
  var dir = block.getFieldValue('DIR') || 'up';
  if (dir === 'down') {
    if (/^-?\d+(\.\d+)?$/.test(delta)) {
      if (delta.charAt(0) === '-') delta = delta.slice(1);
      else if (delta !== '0') delta = '-' + delta;
    } else {
      delta = '-(' + delta + ')';
    }
  }
  return 'macro_engine.scroll(' + delta + ')\n';
};
