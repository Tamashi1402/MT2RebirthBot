// Block: pcr_comment — Python comment(s), one # line per text line
//
// Uses Blockly's built-in Blockly.FieldMultilineInput (the same field the
// separator's label uses) so it's a real text area: grows in width and
// height to fit the text, Enter makes a new line. Click to edit, Tab /
// Escape / click away to finish.
Blockly.Blocks['pcr_comment'] = {
  init: function() {
    this.appendDummyInput()
      .appendField("#")
      .appendField(new Blockly.FieldMultilineInput("comment"), "TEXT");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour(120);
    this.setTooltip("One or more Python comment lines (does not affect execution). Click to edit \u2014 Enter makes a new line and it grows to fit the text.");
  }
};

Blockly.Python['pcr_comment'] = function(block) {
  var raw = (block.getFieldValue('TEXT') || '').replace(/\r\n/g, '\n');
  var lines = raw.split('\n');
  var out = '';
  for (var i = 0; i < lines.length; i++) {
    out += '# ' + lines[i] + '\n';
  }
  return out;
};
