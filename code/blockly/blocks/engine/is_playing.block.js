Blockly.Blocks['pcr_macro_is_playing'] = {
  init: function() {
    this.jsonInit({
      type: "pcr_macro_is_playing",
      message0: "is macro %1 playing",
      args0: [{ type: "input_value", name: "MACRO", check: "String" }],
      inputsInline: true,
      output: "Boolean",
      colour: 210,
      tooltip: "True while that macro path is currently playing."
    });
  }
};
Blockly.Python['pcr_macro_is_playing'] = function(block) {
  var path = Blockly.Python.valueToCode(block, 'MACRO', Blockly.Python.ORDER_NONE) || "''";
  return ['macroforge.engine.functions.call("macroforge.engine.macro.is_playing", ' + path + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};
