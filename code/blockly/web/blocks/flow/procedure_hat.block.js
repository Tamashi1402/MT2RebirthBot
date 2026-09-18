// Block: me_procedure_hat — entry point of a procedure
Blockly.Blocks['me_procedure_hat'] = {
  init: function() {
    this.appendDummyInput()
      .appendField("\u25B6 EVENT")
      .appendField(new Blockly.FieldDropdown([
        ["on start", "on_start"],
        ["on hotkey", "on_hotkey"],
        ["on frame (every frame, ~60/sec)", "on_frame"],
        ["on update (every interval)", "on_update"],
        ["on stop", "on_stop"],
        ["on call (function)", "on_call"],
        ["none (manual call only)", "none"]
      ]), "EVENT_TYPE");

    this.appendDummyInput("INTERVAL_ROW")
      .appendField("every")
      .appendField(new Blockly.FieldNumber(100, 1, 3600000, 1), "INTERVAL")
      .appendField("ms");

    this.appendDummyInput("RETURN_ROW")
      .appendField("return type")
      .appendField(new Blockly.FieldDropdown([
        ["none", "none"], ["number", "number"],
        ["text", "text"], ["logic", "logic"], ["list", "list"]
      ]), "RETURN_TYPE");

    this.setNextStatement(true, null);
    this.setColour(120);
    this.setTooltip("Entry point — defines when this procedure runs");

    // Hide interval/return rows initially (shown via updateVisibility)
    var evt = this.getFieldValue('EVENT_TYPE');
    this.updateIntervalVisibility(evt);
    this.updateReturnTypeVisibility(evt);
  },
  updateIntervalVisibility: function(eventType) {
    var input = this.getInput('INTERVAL_ROW');
    if (input) input.setVisible(eventType === 'on_update');
    try { this.render(); } catch (e) {}
  },
  updateReturnTypeVisibility: function(eventType) {
    var input = this.getInput('RETURN_ROW');
    if (input) input.setVisible(eventType === 'on_call');
    try { this.render(); } catch (e) {}
  },
  // Handle field changes
  onchange: function(event) {
    if (event && event.type === Blockly.Events.BLOCK_CHANGE &&
        event.blockId === this.id && event.name === 'EVENT_TYPE') {
      this.updateIntervalVisibility(event.newValue);
      this.updateReturnTypeVisibility(event.newValue);
    }
  }
};

Blockly.Python['me_procedure_hat'] = function(block) {
  // Hat blocks don't generate code — the generator wrapper handles it
  return '';
};
