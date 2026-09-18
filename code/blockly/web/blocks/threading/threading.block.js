// ╔══════════════════════════════════════════════╗
// ║ Threading blocks — threads, locks             ║
// ║ Ported from MacroEngine                         ║
// ╚══════════════════════════════════════════════╝

// ─── Thread start ───
Blockly.Blocks['me_thread_start'] = {
  init: function() {
    this.appendStatementInput("DO").setCheck(null).appendField("start thread");
    this.setPreviousStatement(true, null); this.setNextStatement(true, null);
    this.setColour(280); this.setTooltip("Start a new thread running the attached code");
  }
};
Blockly.Python['me_thread_start'] = function(b) {
  var doCode = Blockly.Python.statementToCode(b, 'DO') || '  pass\n';
  var clean = doCode.replace(/\s*$/, '');
  var fn = '_me_thread_' + b.id.replace(/[^a-zA-Z0-9_]/g, '_');
  var code = 'def ' + fn + '():\n' + clean + '\n';
  code += 'import threading as _threading\n';
  code += '_t = _threading.Thread(target=' + fn + ', daemon=True)\n';
  code += '_t.start()\n';
  return code;
};

// ─── Thread sleep ───
Blockly.Blocks['me_thread_sleep'] = {
  init: function() {
    this.appendValueInput("SECONDS").setCheck("Number").appendField("thread sleep (seconds)");
    this.setPreviousStatement(true, null); this.setNextStatement(true, null);
    this.setColour(280); this.setTooltip("Sleep in a thread (same as sleep but for threading context)");
  }
};
Blockly.Python['me_thread_sleep'] = function(b) {
  var s = Blockly.Python.valueToCode(b, 'SECONDS', Blockly.Python.ORDER_NONE) || '0';
  return 'time.sleep(' + s + ')\n';
};
