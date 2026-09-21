// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_add_hotkey                         ║
// ║ Category: input                               ║
// ║ Library: keyboard                             ║
// ║ Desc: Register a global hotkey (callback)     ║
// ╚══════════════════════════════════════════════╝

Blockly.Blocks['pcr_add_hotkey'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_add_hotkey",
      "message0": "On hotkey %1 do %2",
      "args0": [
        { "type": "input_value", "name": "KEYS", "check": ["Hotkey", "Key", "String"] },
        { "type": "input_statement", "name": "DO" }
      ],
      "previousStatement": null,
      "nextStatement": null,
      "colour": 40,
      "tooltip": "Register a global hotkey. Plug in create hotkey with (or a single key)."
    });
  }
};

Blockly.Python['pcr_add_hotkey'] = function(block) {
  var keys = (typeof mfKeyCode === 'function' ? mfKeyCode(block, 'KEYS', 'ctrl+c') : (Blockly.Python.valueToCode(block, 'KEYS', Blockly.Python.ORDER_NONE) || '"ctrl+c"'));
  var doCode = Blockly.Python.statementToCode(block, 'DO') || '  pass\n';
  var funcName = 'hotkey_' + block.id.replace(/[^a-zA-Z0-9_]/g, '_');
  var cleanDo = doCode.replace(/\s*$/, '');
  return 'def ' + funcName + '():\n' + cleanDo + '\nkeyboard.add_hotkey(' + keys + ', ' + funcName + ')\n';
};
