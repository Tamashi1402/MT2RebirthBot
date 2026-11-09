// Block: pcr_proc_call — call another procedure (statement)
Blockly.Blocks['pcr_proc_call'] = {
  init: function() {
    this.appendDummyInput()
      .appendField("call")
      .appendField(new Blockly.FieldDropdown(
        function() {
          var procs = window._pcrCallableProcs || [];
          if (procs.length === 0) return [["(no procedures)", ""]];
          return procs.map(function(p) { return [p, p]; });
        }
      ), "PROC_NAME");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour(120);
    this.setTooltip("Call another procedure by name");
  }
};
Blockly.Python['pcr_proc_call'] = function(block) {
  var name = block.getFieldValue('PROC_NAME');
  if (!name) return 'pass\n';
  var fn = 'proc_' + String(name).replace(/[^A-Za-z0-9_]+/g, '_').replace(/^_+|_+$/g, '').replace(/^([0-9])/, '_$1');
  return fn + '()\n';
};

// Block: pcr_proc_call_return — call a procedure and get its return value
Blockly.Blocks['pcr_proc_call_return'] = {
  init: function() {
    this.appendDummyInput()
      .appendField("call and get")
      .appendField(new Blockly.FieldDropdown(
        function() {
          var procs = window._pcrCallableProcs || [];
          if (procs.length === 0) return [["(no procedures)", ""]];
          return procs.map(function(p) { return [p, p]; });
        }
      ), "PROC_NAME");
    this.setOutput(true, null);
    this.setColour(120);
    this.setTooltip("Call a procedure and get its return value");
  }
};
Blockly.Python['pcr_proc_call_return'] = function(block) {
  var name = block.getFieldValue('PROC_NAME');
  if (!name) return ['None', Blockly.Python.ORDER_ATOMIC];
  var fn = 'proc_' + String(name).replace(/[^A-Za-z0-9_]+/g, '_').replace(/^_+|_+$/g, '').replace(/^([0-9])/, '_$1');
  return [fn + '()', Blockly.Python.ORDER_FUNCTION_CALL];
};
