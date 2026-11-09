// ╔══════════════════════════════════════════════╗
// ║ Blocks: resource location helpers              ║
// ║ Category: components                           ║
// ║  - string -> resource location                  ║
// ║  - path of resource location -> string          ║
// ║  - resource location from mode config           ║
// ╚══════════════════════════════════════════════╝

Blockly.Blocks['pcr_str_to_resloc'] = {
  init: function() {
    this.appendValueInput('STR')
      .setCheck('String')
      .appendField('string to resource location');
    this.setOutput(true, ['String', 'RESLOC']);
    this.setColour(270);
    this.setTooltip('Turn text (res://name, or any path) into a resource location.');
  }
};
Blockly.Python['pcr_str_to_resloc'] = function(block) {
  var s = Blockly.Python.valueToCode(block, 'STR', Blockly.Python.ORDER_NONE) || "''";
  return ['resloc(' + s + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};

Blockly.Blocks['pcr_resloc_to_str'] = {
  init: function() {
    this.appendValueInput('LOC')
      .setCheck(['String', 'RESLOC'])
      .appendField('path of resource location');
    this.setOutput(true, 'String');
    this.setColour(160);
    this.setTooltip('The resolved filesystem path of a resource location, as text.');
  }
};
Blockly.Python['pcr_resloc_to_str'] = function(block) {
  var loc = Blockly.Python.valueToCode(block, 'LOC', Blockly.Python.ORDER_NONE) || "''";
  return ['resloc_str(' + loc + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};

Blockly.Blocks['pcr_resloc_from_config'] = {
  init: function() {
    this.appendDummyInput()
      .appendField('resource location from mode config')
      .appendField(new Blockly.FieldDropdown(function () {
        var items = (window._mfMappings && window._mfMappings.config) || [];
        var opts = [], seen = {};
        items.forEach(function (it) {
          if (!it || !it.id || seen[it.id]) return;
          var t = it.type || 'string';
          if (t === 'bool' || t === 'logic') t = 'boolean';
          if (t === 'number') t = 'number';
          if (t !== 'string') return;
          seen[it.id] = true;
          opts.push([it.label || it.id, it.id]);
        });
        var cur = this.getValue && this.getValue();
        if (cur && !seen[cur]) opts.unshift([cur, cur]);
        if (!opts.length) opts.push(['(none)', '']);
        return opts;
      }), 'ID');
    this.setOutput(true, ['String', 'RESLOC']);
    this.setColour(270);
    this.setTooltip('Use a string value from the mode config as a resource location.');
  }
};
Blockly.Python['pcr_resloc_from_config'] = function(block) {
  var id = JSON.stringify(block.getFieldValue('ID') || '');
  return ['resloc(macroforge.engine.config.get(' + id + '))', Blockly.Python.ORDER_FUNCTION_CALL];
};
