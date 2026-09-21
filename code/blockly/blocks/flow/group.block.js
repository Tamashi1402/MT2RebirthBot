// Block: pcr_group — named collapsible container for flow blocks
// 1:1 with the macro editor's mfm_group: ONE block on the canvas, its
// blocks live inside a mutator-style popup window (own workspace) —
// click ✎ edit to open them. Everything is LIVE-synced: dragging blocks
// in or out of the window moves them for real; the badge and the saved
// data update as you edit. Generated Python runs the inner blocks
// exactly as if they sat at the group's position — plus a comment
// header naming the group. Usable anywhere statements go: procedures,
// functions, loops, condition bodies.
//
// Storage: the inner blocks serialize as XML in the mutation:
//   <mutation innerxml="...">&lt;block .../&gt;...</mutation>
// (Blockly escapes the attribute). The chain lives under a
// pcr_group_hat cap INSIDE the popup; loose chains parked by the user
// are kept as top-level blocks marked stray="1" and are NOT run.

// clickable '✎ edit' label — same pattern as the macro editor's group
function mfGroupEditField() {
  var field = new Blockly.FieldLabel('\u270e edit');
  field.EDITABLE = true;
  field.SERIALIZABLE = false;
  field.showEditor_ = function () {
    if (window.__mfOpenGroup) window.__mfOpenGroup(this.sourceBlock_);
  };
  return field;
}

Blockly.Blocks['pcr_group'] = {
  init: function() {
    this.appendDummyInput()
      .appendField('Group', 'GROUPLBL')
      .appendField(new Blockly.FieldTextInput('section'), 'NAME')
      .appendField(mfGroupEditField(), 'EDIT')
      .appendField('', 'STEPS');
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour(120);   // Flow colour — same hue as separator/label/goto
    this.setTooltip('Named container for a run of blocks \u2014 the blocks live inside; click edit to open them in their own window. Runs the inner blocks exactly as if they were here.');
    this.mfInnerXml = '';   // inner blocks XML (hat chain + parked strays)
    this.mfmSteps = [];     // never used; kept so old code paths treat us as inert
  },
  domToMutation: function(el) {
    try { this.mfInnerXml = el.getAttribute('innerxml') || ''; }
    catch (e) { this.mfInnerXml = ''; }
    this.mfUpdateBadge();
  },
  mutationToDom: function() {
    var m = document.createElement('mutation');
    try { m.setAttribute('innerxml', this.mfInnerXml || ''); }
    catch (e) { m.setAttribute('innerxml', ''); }
    return m;
  },
  mfUpdateBadge: function() {
    var n = 0;
    try {
      n = mfGroupCountChain(this.mfInnerXml || '');
    } catch (e) { n = 0; }
    try { this.setFieldValue(n === 1 ? '(1 block)' : ('(' + n + ' blocks)'), 'STEPS'); } catch (e) {}
  },
  mfSetInnerXml: function(xml) {
    this.mfInnerXml = xml || '';
    this.mfUpdateBadge();
  },
};

// Group hat — the cap INSIDE the group edit window (says "Group <name>").
// Same shape as the procedure hat; the window syncs its NAME back to the
// group block. Popup-only: never in the toolbox (EXCLUDED).
Blockly.Blocks['pcr_group_hat'] = {
  init: function() {
    this.appendDummyInput()
      .appendField('Group')
      .appendField(new Blockly.FieldTextInput('section'), 'NAME');
    this.appendStatementInput('DO').setCheck(null);
    this.setPreviousStatement(false);
    this.setNextStatement(false);
    this.setDeletable(false);
    this.setMovable(true);
    this.hat = 'cap';
    this.setColour(120);
    this.setTooltip('Blocks inside this group. Drag blocks in or out \u2014 the group on the main canvas updates live.');
  },
};

// ── shared XML helpers ──────────────────────────────────────────────
// count the blocks chained under the hat (strays excluded — they park,
// they don't run), for the badge.
function mfGroupCountChain(innerXml) {
  if (!innerXml || !innerXml.replace) return 0;
  try {
    var dom = (function (t) { var u = (typeof Blockly !== 'undefined') && Blockly.utils; var f = (u && u.xml && u.xml.textToDom) || (Blockly.Xml && Blockly.Xml.textToDom); return f ? f(t) : null; })('<xml>' + innerXml + '</xml>');
    var hat = null;
    var kids = dom.children || [];
    for (var i = 0; i < kids.length; i++) {
      if (kids[i].nodeName === 'block' && kids[i].getAttribute('type') === 'pcr_group_hat') { hat = kids[i]; break; }
    }
    if (!hat) return 0;
    // querySelectorAll walks DESCENDANTS only — the hat itself is never
    // included, so this is exactly the chain length (strays sit outside
    // the hat element and are never reached)
    var all = hat.querySelectorAll ? hat.querySelectorAll('block') : [];
    return Math.max(0, all.length);
  } catch (e) { return 0; }
}

// Python — the hat itself contributes nothing (it is a popup-only cap)
Blockly.Python['pcr_group_hat'] = function(block) {
  return '';
};

// Python — inline the group's chain at base indent. The parent's
// scrub_/statementToCode indents the whole return like any statement,
// so the inner blocks end up exactly where they would have been.
Blockly.Python['pcr_group'] = function(block) {
  var name = (block.getFieldValue('NAME') || 'group').trim() || 'group';
  var code = '';
  var innerXml = block.mfInnerXml || '';
  if (innerXml) {
    var dom = null;
    try { dom = (function (t) { var u = (typeof Blockly !== 'undefined') && Blockly.utils; var f = (u && u.xml && u.xml.textToDom) || (Blockly.Xml && Blockly.Xml.textToDom); return f ? f(t) : null; })('<xml>' + innerXml + '</xml>'); } catch (e) { dom = null; }
    if (dom) {
      var hatChild = null;
      var kids = dom.children || [];
      for (var i = 0; i < kids.length; i++) {
        if (kids[i].nodeName === 'block' && kids[i].getAttribute('type') === 'pcr_group_hat') { hatChild = kids[i]; break; }
      }
      if (hatChild) {
        var tws = new Blockly.Workspace();
        try {
          var hatBlock = Blockly.Xml.domToBlock(hatChild, tws);
          var head = hatBlock && hatBlock.getInputTargetBlock && hatBlock.getInputTargetBlock('DO');
          // blockToCode generates the head AND the whole chain after it
          // (scrub_); helpers via provideFunction_ still land in the
          // outer definitions, exactly like canvas blocks.
          if (head) code = Blockly.Python.blockToCode(head);
        } catch (e) {
          code = '# group ' + name + ': could not generate (' + (e && e.message ? e.message : e) + ')\n';
        } finally { try { tws.dispose(); } catch (e2) {} }
      }
    }
  }
  if (!code) return '# \u2500\u2500 group: ' + name + ' \u2500\u2500\n';
  return '# \u2500\u2500 group: ' + name + ' \u2500\u2500\n' + code.replace(/\s+$/, '\n');
};
