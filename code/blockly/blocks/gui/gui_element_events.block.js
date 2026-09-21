// ╔════════════════════════════════════════════╗
// ║ Block: GUI element events                   ║
// ║ Category: GUI → Elements (dark green)       ║
// ║ Desc: "When <kind> id <id> ..." — a FLOATING  ║
// ║ block like a function definition (no flow    ║
// ║ connectors, no hat). Fires for ANY GUI window ║
// ║ with that element id, even ones created in    ║
// ║ another procedure. Sentinel markers hoist the ║
// ║ def + registration to module level — armed    ║
// ║ at compile, no need to be in the flow.        ║
// ║                                              ║
// ║ NOTE: every block is defined EXPLICITLY —   ║
// ║ the dashboard toolbox scan greps for literal ║
// ║ Blockly.Blocks['names'] to know what exists.║
// ╚════════════════════════════════════════════╝

/* the "do as" socket gets an auto-locked GUI element iterator (see
   mfInstallGuielIterLock in gui_element_core.block.js). The handler
   receives the element that fired as mf_guiel_iter. */

function _mfGuielEventDef(kind, verb, tooltip) {
  return {
    init: function () {
      this.appendDummyInput().appendField('When ' + kind + ' id');
      this.appendValueInput('ID').setCheck('String');
      this.appendDummyInput().appendField(verb + ' do as');
      this.appendValueInput('ITER').setCheck('GuiElem');
      this.appendStatementInput('DO');
      // floats freely like a function block — no flow connectors, no hat
      this.setPreviousStatement(false);
      this.setNextStatement(false);
      this.setInputsInline(true);
      this.setColour(PCR_GUIEL_COLOUR);
      this.setTooltip(tooltip);
    }
  };
}

Blockly.Blocks['pcr_guiel_on_button'] = _mfGuielEventDef('button', 'clicked',
  'Runs the blocks inside whenever the button with this id is clicked — in ANY GUI window, even one created in another procedure. The GUI element iterator is the button that fired. Floats freely like a function block — it does NOT need to be in the flow. When the macro starts, the handler is registered automatically.');

Blockly.Blocks['pcr_guiel_on_checkbox'] = _mfGuielEventDef('checkbox', 'changed',
  'Runs the blocks inside whenever the checkbox with this id is toggled — in ANY GUI window, even one created in another procedure. The GUI element iterator is the checkbox that fired. Floats freely like a function block — it does NOT need to be in the flow. When the macro starts, the handler is registered automatically.');

Blockly.Blocks['pcr_guiel_on_combobox'] = _mfGuielEventDef('combobox', 'changed',
  'Runs the blocks inside whenever the combobox with this id gets a new selection — in ANY GUI window, even one created in another procedure. The GUI element iterator is the combobox that fired. Floats freely like a function block — it does NOT need to be in the flow. When the macro starts, the handler is registered automatically.');

Blockly.Blocks['pcr_guiel_on_list'] = _mfGuielEventDef('list', 'changed',
  'Runs the blocks inside whenever the selection of the list with this id changes — in ANY GUI window, even one created in another procedure. The GUI element iterator is the list that fired. Floats freely like a function block — it does NOT need to be in the flow. When the macro starts, the handler is registered automatically.');

Blockly.Blocks['pcr_guiel_on_text_area'] = _mfGuielEventDef('text area', 'changed',
  'Runs the blocks inside whenever the text of the text area with this id changes (typing, deleting...) — in ANY GUI window, even one created in another procedure. The GUI element iterator is the text area that fired. Floats freely like a function block — it does NOT need to be in the flow. When the macro starts, the handler is registered automatically.');

Blockly.Blocks['pcr_guiel_on_inputfield'] = _mfGuielEventDef('inputfield', 'changed',
  'Runs the blocks inside whenever the text of the inputfield with this id changes (typing, deleting...) — in ANY GUI window, even one created in another procedure. The GUI element iterator is the inputfield that fired. Floats freely like a function block — it does NOT need to be in the flow. When the macro starts, the handler is registered automatically.');

Blockly.Blocks['pcr_guiel_on_slider'] = _mfGuielEventDef('slider', 'changed',
  'Runs the blocks inside whenever the slider with this id moves — in ANY GUI window, even one created in another procedure. The GUI element iterator is the slider that fired. Floats freely like a function block — it does NOT need to be in the flow. When the macro starts, the handler is registered automatically.');

function _mfGuielEventGen(kind) {
  return function (block) {
    var id = Blockly.Python.valueToCode(block, 'ID', Blockly.Python.ORDER_NONE) || "''";
    var doCode = Blockly.Python.statementToCode(block, 'DO') || '  pass\n';
    var funcName = '_mf_guiel_evt_' + block.id.replace(/[^a-zA-Z0-9_]/g, '_');
    var cleanDo = doCode.replace(/\s*$/, '');
    // Sentinel markers (same as the function block) hoist the def +
    // registration to MODULE level of the procedure namespace — the
    // handler exists and is armed as soon as the macro compiles, like a
    // function definition, instead of needing to run inside the flow.
    return '#@@PCR_FUNC_DEF@@\n'
      + 'def ' + funcName + '(mf_guiel_iter):\n' + cleanDo
      + '\nguiel_on(\'' + kind + '\', ' + id + ', ' + funcName + ')\n'
      + '#@@PCR_FUNC_DEF_END@@\n';
  };
}

Blockly.Python['pcr_guiel_on_button'] = _mfGuielEventGen('button');
Blockly.Python['pcr_guiel_on_checkbox'] = _mfGuielEventGen('checkbox');
Blockly.Python['pcr_guiel_on_combobox'] = _mfGuielEventGen('combobox');
Blockly.Python['pcr_guiel_on_list'] = _mfGuielEventGen('list');
Blockly.Python['pcr_guiel_on_text_area'] = _mfGuielEventGen('text_area');
Blockly.Python['pcr_guiel_on_inputfield'] = _mfGuielEventGen('inputfield');
Blockly.Python['pcr_guiel_on_slider'] = _mfGuielEventGen('slider');
