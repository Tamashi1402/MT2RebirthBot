// Block: pcr_separator — visual separator with comment + inner blocks
// A collapsible container that wraps a group of blocks, with a comment
// label. Generates as a Python comment header + the inner code.
//
// The label uses Blockly's own built-in Blockly.FieldMultilineInput (the
// same field already used by the "code" snippet block in mf-plugins.js)
// so it grows in width AND height to fit the text and Enter inserts a new
// line. Click the label, type, Escape/Tab/click-away to finish.
//
// History: an earlier version of this file used a hand-rolled multiline
// field. It computed its own size but never told the BLOCK to re-render,
// so the block's outer boundary never grew to match — the label's text
// grew while the green block outline stayed fixed, and the text spilled
// out past it. Blockly.FieldMultilineInput is core, tested code that
// keeps the block boundary in sync with the field automatically, so that
// class of bug can't happen here now.

Blockly.Blocks['pcr_separator'] = {
  init: function() {
    this.appendDummyInput("HEADER")
      .appendField("\u2500\u2500\u2500")  // ───
      .appendField(new Blockly.FieldMultilineInput("section"), "COMMENT")
      .appendField("\u2500\u2500\u2500");
    this.appendStatementInput("DO")
      .setCheck(null);
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour(120);
    this.setTooltip(
      "A collapsible separator with a comment. Click the label to edit \u2014 Enter makes a new line and the label grows to fit the text."
    );
  }
};

Blockly.Python['pcr_separator'] = function(block) {
  var raw = (block.getFieldValue('COMMENT') || '').replace(/\r\n/g, '\n');
  var lines = raw.split('\n')
    .map(function(s) { return s.trim(); })
    .filter(function(s) { return s.length > 0; });
  if (!lines.length) lines = ['section'];
  // each label line becomes its own '# ─── ... ───' comment header
  var line = '';
  for (var i = 0; i < lines.length; i++) {
    line += '# \u2500\u2500\u2500 ' + lines[i] + ' \u2500\u2500\u2500\n';
  }
  // Emit the inner chain UNPREFIXED via blockToCode (same pattern as
  // pcr_group / the procedure hat). The parent's statementToCode indents
  // this whole return once, so the comment header and the wrapped blocks
  // land at the SAME level — exactly where the blocks would sit without
  // the separator.
  // The old version used statementToCode(block, 'DO'), which added a
  // SECOND INDENT to the wrapped chain: every block inside a separator
  // came out one level too deep and broke the generated Python
  // (IndentationError on procedures using separators).
  var target = block.getInputTargetBlock('DO');
  var inner = '';
  if (target) {
    try {
      var generated = Blockly.Python.blockToCode(target);
      if (typeof generated === 'string') inner = generated;
    } catch (e) {
      inner = '# separator \'' + lines.join(' / ') + '\': could not generate inner blocks\n';
    }
  }
  if (!inner) inner = 'pass\n';
  return line + inner;
};
