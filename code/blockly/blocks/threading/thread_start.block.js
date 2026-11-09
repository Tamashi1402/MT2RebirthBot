Blockly.Blocks['pcr_thread_start'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_thread_start", "message0": "Start thread do %1",
      "args0": [{ "type": "input_statement", "name": "DO" }],
      "previousStatement": null, "nextStatement": null, "colour": 150,
      "tooltip": "Run code in a daemon background thread. Stop (F9) flags the thread via stopped()."
    });
  }
};

Blockly.Python['pcr_thread_start'] = function(block) {
  var doCode = Blockly.Python.statementToCode(block, 'DO') || '    pass\n';
  Blockly.Python._mfmBgSeq = (Blockly.Python._mfmBgSeq || 0) + 1;
  var funcName = 'worker_' + Blockly.Python._mfmBgSeq;
  var cleanDo = doCode.replace(/\s*$/, '');
  return (
    'def ' + funcName + '():\n' +
    cleanDo + '\n' +
    'threading.Thread(target=' + funcName + ', daemon=True, name=' + JSON.stringify(funcName) + ').start()\n'
  );
};
