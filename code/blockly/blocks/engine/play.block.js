// Block: pcr_macro_play — play a .macro by path
// "wait until finished" (default ON) makes the procedure WAIT until the
// macro finishes before the next block runs. Uncheck it for the old
// fire-and-forget behavior (macro plays in the background, flow races on).
Blockly.Blocks['pcr_macro_play'] = {
  init: function() {
    this.jsonInit({
      type: "pcr_macro_play",
      message0: "play macro %1 wait until finished %2",
      args0: [
        { type: "input_value", name: "MACRO", check: "String" },
        { type: "field_checkbox", name: "WAIT", checked: true }
      ],
      inputsInline: true,
      previousStatement: null,
      nextStatement: null,
      colour: 210,
      tooltip: "Play a .macro by path. 'wait until finished' ON (default): the next block runs only after the macro is done. OFF: the macro plays in the background and the flow continues immediately.",
    });
  }
};
Blockly.Python['pcr_macro_play'] = function(block) {
  var path = Blockly.Python.valueToCode(block, 'MACRO', Blockly.Python.ORDER_NONE) || "''";
  var wait = String(block.getFieldValue('WAIT')).toUpperCase() === 'TRUE' ? 'True' : 'False';
  return 'macroforge.engine.functions.call("macroforge.engine.macro.play", ' + path + ', ' + wait + ')\n';
};
