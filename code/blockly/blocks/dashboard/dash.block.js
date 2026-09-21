/* MacroForge dashboard blocks — graph series, dashboard values (run tab widgets). */
(function () {
  function widgetMenu(kind) {
    return function () {
      var items = (window._mfMappings && window._mfMappings[kind || 'dashboard']) || [];
      var opts = [];
      var seen = {};
      items.forEach(function (it) {
        if (!it || !it.id || seen[it.id]) return;
        seen[it.id] = 1;
        opts.push([it.label || it.id, it.id]);
      });
      var cur = this.getValue && this.getValue();
      if (cur && !seen[cur]) opts.unshift([cur, cur]);
      if (!opts.length) opts.push(['(no widget)', '']);
      return opts;
    };
  }

  Blockly.Blocks['mf_graph_push'] = {
    init: function () {
      this.appendDummyInput()
        .appendField('push graph')
        .appendField(new Blockly.FieldDropdown(widgetMenu('dashboard')), 'WID');
      this.appendValueInput('VALUE').setCheck('Number').appendField('value');
      this.setPreviousStatement(true, null);
      this.setNextStatement(true, null);
      this.setInputsInline(true);
      this.setColour(260);
      this.setTooltip('Append a point to a Graph widget\'s live series.');
    }
  };
  Blockly.Python['mf_graph_push'] = function (b) {
    var id = JSON.stringify(b.getFieldValue('WID') || '');
    var v = Blockly.Python.valueToCode(b, 'VALUE', Blockly.Python.ORDER_NONE) || '0';
    return 'macroforge.engine.graph.push(' + id + ', ' + v + ')\n';
  };

  Blockly.Blocks['mf_graph_clear'] = {
    init: function () {
      this.appendDummyInput()
        .appendField('clear graph')
        .appendField(new Blockly.FieldDropdown(widgetMenu('dashboard')), 'WID');
      this.setPreviousStatement(true, null);
      this.setNextStatement(true, null);
      this.setColour(260);
      this.setTooltip('Erase a Graph widget\'s series.');
    }
  };
  Blockly.Python['mf_graph_clear'] = function (b) {
    var id = JSON.stringify(b.getFieldValue('WID') || '');
    return 'macroforge.engine.graph.clear(' + id + ')\n';
  };

  Blockly.Blocks['mf_graph_stat'] = {
    init: function () {
      this.appendDummyInput()
        .appendField('graph')
        .appendField(new Blockly.FieldDropdown(widgetMenu('dashboard')), 'WID')
        .appendField(new Blockly.FieldDropdown([['last value', 'last'], ['minimum', 'min'], ['maximum', 'max'], ['average', 'avg'], ['point count', 'count']]), 'KIND');
      this.setOutput(true, 'Number');
      this.setInputsInline(true);
      this.setColour(260);
      this.setTooltip('Live statistic of a Graph widget\'s series.');
    }
  };
  Blockly.Python['mf_graph_stat'] = function (b) {
    var id = JSON.stringify(b.getFieldValue('WID') || '');
    var kind = JSON.stringify(b.getFieldValue('KIND') || 'last');
    return ['macroforge.engine.graph.stat(' + id + ', ' + kind + ')', Blockly.Python.ORDER_FUNCTION_CALL];
  };

  Blockly.Blocks['mf_set_dash_value'] = {
    init: function () {
      this.appendDummyInput()
        .appendField('set dashboard value')
        .appendField(new Blockly.FieldDropdown(widgetMenu('dashboard')), 'ID');
      this.appendValueInput('VALUE').setCheck(null).appendField('to');
      this.setPreviousStatement(true, null);
      this.setNextStatement(true, null);
      this.setInputsInline(true);
      this.setColour(260);
      this.setTooltip('Write a live value into a dashboard widget (read it back with get dashboard value, or wire it into conditions).');
    }
  };
  Blockly.Python['mf_set_dash_value'] = function (b) {
    var id = JSON.stringify(b.getFieldValue('ID') || '');
    var v = Blockly.Python.valueToCode(b, 'VALUE', Blockly.Python.ORDER_NONE) || '0';
    return 'macroforge.engine.dashboard.set(' + id + ', ' + v + ')\n';
  };
})();
