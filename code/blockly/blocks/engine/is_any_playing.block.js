// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_macro_is_any_playing              ║
// ║ Category: macro_engine                        ║
// ║ Desc: Is ANY macro currently playing (bool)   ║
// ╚══════════════════════════════════════════════╝

// ─── Definition ───
Blockly.Blocks['pcr_macro_is_any_playing'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_macro_is_any_playing",
      "message0": "is any macro currently playing",
      "output": "Boolean",
      "colour": 210,
      "tooltip": "True while any macro is playing, false when nothing is running. Useful for guarding play-macro calls (e.g. only start one if nothing else is running)."
    });
  }
};

// ─── Python Generator ───
Blockly.Python['pcr_macro_is_any_playing'] = function(block) {
  return ['macro_engine.is_any_macro_playing()', Blockly.Python.ORDER_ATOMIC];
};
