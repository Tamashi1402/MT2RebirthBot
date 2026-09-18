// Block: me_proc_call — call another procedure
Blockly.Blocks['me_proc_call'] = {
  init: function() {
    this.appendDummyInput()
      .appendField("call")
      .appendField(new Blockly.FieldDropdown(
        function() {
          var procs = window._meCallableProcs || [];
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
Blockly.Python['me_proc_call'] = function(block) {
  var name = block.getFieldValue('PROC_NAME');
  if (!name) return 'pass\n';
  var fn = 'proc_' + name.replace(/ /g, '_').replace(/-/g, '_');
  return fn + '()\n';
};

// Block: me_proc_call_return — call a procedure and get its return value
Blockly.Blocks['me_proc_call_return'] = {
  init: function() {
    this.appendDummyInput()
      .appendField("call and get")
      .appendField(new Blockly.FieldDropdown(
        function() {
          var procs = window._meCallableProcs || [];
          if (procs.length === 0) return [["(no procedures)", ""]];
          return procs.map(function(p) { return [p, p]; });
        }
      ), "PROC_NAME");
    this.setOutput(true, null);
    this.setColour(120);
    this.setTooltip("Call a procedure and get its return value");
  }
};
Blockly.Python['me_proc_call_return'] = function(block) {
  var name = block.getFieldValue('PROC_NAME');
  if (!name) return ['None', Blockly.Python.ORDER_NONE];
  var fn = 'proc_' + name.replace(/ /g, '_').replace(/-/g, '_');
  return [fn + '()', Blockly.Python.ORDER_FUNCTION_CALL];
};
