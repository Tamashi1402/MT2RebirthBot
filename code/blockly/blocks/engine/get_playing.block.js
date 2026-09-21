// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_macro_get_playing                  ║
// ║ Category: macro_engine                       ║
// ║ Desc: Name of the currently playing macro    ║
// ╚══════════════════════════════════════════════╝

// ─── Definition ───
Blockly.Blocks['pcr_macro_get_playing'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_macro_get_playing",
      "message0": "currently playing macro",
      "output": "String",
      "colour": 160,
      "tooltip": "Returns the name of the macro that is currently playing (no .macro in the name). Empty string when nothing is playing"
    });
  }
};

// ─── Python Generator ───
Blockly.Python['pcr_macro_get_playing'] = function(block) {
  return ['macro_engine.get_playing_macro()', Blockly.Python.ORDER_ATOMIC];
};
