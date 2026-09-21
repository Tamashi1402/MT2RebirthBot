// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_procedure_hat                        ║
// ║ Category: base/flow (excluded from toolbox —   ║
// ║   auto-inserted once per procedure workspace)   ║
// ║ Desc: Hat = entry point. Events live on the     ║
// ║   flow canvas (Start / Stop / Update / Any).    ║
// ║   Return type comes from a return block.        ║
// ╚══════════════════════════════════════════════╝

Blockly.Blocks['pcr_procedure_hat'] = {
  init: function() {
    this.appendDummyInput()
      .appendField("procedure");

    this.appendStatementInput("DO")
      .setCheck(null);

    this.setPreviousStatement(false);
    this.setNextStatement(false);
    this.setDeletable(false);
    this.setMovable(true);

    this.hat = 'cap';
    this.setTooltip(
      "Entry point of this procedure.\n" +
      "Start / Stop / Update live on the flow canvas — not here.\n" +
      "Use a return block to send a value (required for line conditions)."
    );
    this.setHelpUrl("");
    this.setColour(120);
  }
};

if (Blockly.Python) {
  // NB: statementToCode() prefixes the branch with Blockly.Python.INDENT —
  // that leak used to indent the whole procedure body 2 spaces while the
  // variable preamble sat at column 0, which broke compilation of every
  // procedure that used variables. Generate the chain at column 0 instead.
  Blockly.Python['pcr_procedure_hat'] = function(block) {
    var target = block.getInputTargetBlock('DO');
    if (!target) return '';
    var code = Blockly.Python.blockToCode(target);
    return (typeof code === 'string') ? code : '';
  };
  Blockly.Python['me_procedure_hat'] = Blockly.Python['pcr_procedure_hat'];
}
Blockly.Blocks['me_procedure_hat'] = Blockly.Blocks['pcr_procedure_hat'];
