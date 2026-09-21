// running / documents locations (string colour 160)

Blockly.Blocks['pcr_path_running'] = {
  init: function() {
    this.jsonInit({
      type: "pcr_path_running",
      message0: "running location",
      output: "String",
      colour: 160,
      tooltip: "Root folder of the running app (exe / START.bat)."
    });
  }
};
Blockly.Python['pcr_path_running'] = function() {
  return ['macroforge.engine.functions.call("macroforge.engine.path.running")', Blockly.Python.ORDER_FUNCTION_CALL];
};

// Alias: original PYCreator "App directory" is the same root.
Blockly.Blocks['pcr_path_appdir'] = Blockly.Blocks['pcr_path_running'];
Blockly.Python['pcr_path_appdir'] = Blockly.Python['pcr_path_running'];

Blockly.Blocks['pcr_path_documents'] = {
  init: function() {
    this.jsonInit({
      type: "pcr_path_documents",
      message0: "documents location",
      output: "String",
      colour: 160,
      tooltip: "User Documents folder."
    });
  }
};
Blockly.Python['pcr_path_documents'] = function() {
  return ['macroforge.engine.functions.call("macroforge.engine.path.documents")', Blockly.Python.ORDER_FUNCTION_CALL];
};
