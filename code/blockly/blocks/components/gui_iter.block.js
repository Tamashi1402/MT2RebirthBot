/* ── gui iterator (value block) ──
   Inside a "For each active GUI do" loop: the GUI window of the current
   iteration. Output is Gui-typed, so it plugs into any GUI socket. */
Blockly.Blocks['pcr_gui_iter'] = {
  init: function () {
    this.appendDummyInput().appendField('GUI iterator');
    this.setOutput(true, 'Gui');
    this.setColour('#2f9e44');
    this.setTooltip('The current GUI window inside a \u201CFor each active GUI do\u201D loop. Inside the loop it is locked in place \u2014 right-click it and choose Duplicate to get a free copy for other GUI sockets. You can also drag a fresh one from GUI \u2192 Data.');
  }
};
Blockly.Python['pcr_gui_iter'] = function () {
  return ['mf_gui_iter', Blockly.Python.ORDER_ATOMIC];
};
