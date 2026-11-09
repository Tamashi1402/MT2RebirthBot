Blockly.Blocks['pcr_timer'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_timer",
      "message0": "After %1 ms do %2",
      "args0": [
        { "type": "input_value", "name": "SECONDS", "check": "Number" },
        { "type": "input_statement", "name": "DO" }
      ],
      "previousStatement": null, "nextStatement": null, "colour": 120,
      "tooltip": "Run code after a delay in milliseconds (daemon timer). Honours Stop (F9)."
    });
  }
};

Blockly.Python['pcr_timer'] = function(block) {
  var secs = Blockly.Python.valueToCode(block, 'SECONDS', Blockly.Python.ORDER_NONE) || '1';
  var doCode = Blockly.Python.statementToCode(block, 'DO') || '    pass\n';
  Blockly.Python._mfmBgSeq = (Blockly.Python._mfmBgSeq || 0) + 1;
  var fn = 'after_' + Blockly.Python._mfmBgSeq;
  return (
    'def ' + fn + '():\n' +
    '    if stopped():\n' +
    '        return\n' +
    doCode +
    'threading.Timer((' + secs + ') / 1000.0, ' + fn + ').start()\n'
  );
};
