Blockly.Blocks['pcr_macro_stop'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_macro_stop",
      "message0": "Stop currently playing macro",
      "previousStatement": null,
      "nextStatement": null,
      "colour": 210,
      "tooltip": "Same as Stop (F9) for the playing macro: halt playback and release held keys."
    });
  }
};

Blockly.Python['pcr_macro_stop'] = function(block) {
  return (
    'try:\n' +
    '    macroforge.engine.functions.call("macroforge.engine.macro.stop")\n' +
    'except Exception:\n' +
    '    try:\n' +
    '        import bot as _bot\n' +
    '        _bot._on_f9()\n' +
    '    except Exception:\n' +
    '        pass\n'
  );
};
