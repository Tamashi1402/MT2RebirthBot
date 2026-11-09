// ╔══════════════════════════════════════════════╗
// ║ Block: Typed variable GET blocks               ║
// ║ Category: Variables                           ║
// ║    get number (230) / get text (160)          ║
// ║    get logic  (210) / get list (260)          ║
// ║ PYCreator 1:1 — dropdown Global: / Local:     ║
// ╚══════════════════════════════════════════════╝

var PCR_VAR_COLOURS = {
  text: 160,
  number: 230,
  logic: 210,
  list: 260,
  color: 20,
  image: 300,
  resloc: 270,
  gui: '#2f9e44',
  guiel: '#257b35'
};

function _pcrPyName(raw) {
  var n = (raw || '').trim().replace(/[^A-Za-z0-9_]/g, '_');
  if (/^[0-9]/.test(n)) n = '_' + n;
  return n;
}

function pcrVarDropdownOptions(varType, current) {
  var options = [];
  var seen = {};
  function add(label, value) {
    if (!value || seen[value]) return;
    seen[value] = true;
    options.push([label, value]);
  }

  var globalVars = window._pcrGlobalVars || {};
  for (var name in globalVars) {
    if (globalVars[name] === varType) add('Global: ' + name, name);
  }

  var localVars = window._pcrLocalVars || {};
  for (var lname in localVars) {
    if (localVars[lname] === varType) add('Local: ' + lname, lname);
  }

  var PCR_PARAM_LOOKUP_TYPE = { text: 'string', number: 'number', logic: 'bool' };
  var wantParamType = PCR_PARAM_LOOKUP_TYPE[varType];
  if (wantParamType) {
    var funcParams = window._pcrFuncParams || {};
    for (var pname in funcParams) {
      if (funcParams[pname] === wantParamType) add('Param: ' + pname, pname);
    }
  }

  var ghosts = window._pcrGhostVars || {};
  for (var gname in ghosts) {
    if (ghosts[gname] === varType) add(gname, gname);
  }
  if (current) add(current, current);

  if (!options.length) options.push(['(no variables of this type)', '']);
  return options;
}

function pcrVarDropdown(varType) {
  return new Blockly.FieldDropdown(function () {
    return pcrVarDropdownOptions(varType, this.getValue && this.getValue());
  });
}

Blockly.Blocks['pcr_get_text'] = {
  init: function () {
    this.appendDummyInput()
      .appendField('get text')
      .appendField(pcrVarDropdown('text'), 'VAR');
    this.setOutput(true, 'String');
    this.setColour(160);
    this.setTooltip('Get a text (string) variable.');
  }
};

Blockly.Blocks['pcr_get_number'] = {
  init: function () {
    this.appendDummyInput()
      .appendField('get number')
      .appendField(pcrVarDropdown('number'), 'VAR');
    this.setOutput(true, 'Number');
    this.setColour(230);
    this.setTooltip('Get a number variable.');
  }
};

Blockly.Blocks['pcr_get_logic'] = {
  init: function () {
    this.appendDummyInput()
      .appendField('get logic')
      .appendField(pcrVarDropdown('logic'), 'VAR');
    this.setOutput(true, 'Boolean');
    this.setColour(210);
    this.setTooltip('Get a boolean variable.');
  }
};

Blockly.Blocks['pcr_get_list'] = {
  init: function () {
    this.appendDummyInput()
      .appendField('get list')
      .appendField(pcrVarDropdown('list'), 'VAR');
    this.setOutput(true, 'Array');
    this.setColour(260);
    this.setTooltip('Get a list variable.');
  }
};

Blockly.Blocks['pcr_get_image'] = {
  init: function () {
    this.appendDummyInput()
      .appendField('get image')
      .appendField(pcrVarDropdown('image'), 'VAR');
    this.setOutput(true, 'Image');
    this.setColour(PCR_VAR_COLOURS.image);
    this.setTooltip('Get an image variable (a loaded PIL image).');
  }
};

Blockly.Blocks['pcr_get_resloc'] = {
  init: function () {
    this.appendDummyInput()
      .appendField('get resource location')
      .appendField(pcrVarDropdown('resloc'), 'VAR');
    this.setOutput(true, ['String', 'RESLOC']);
    this.setColour(PCR_VAR_COLOURS.resloc);
    this.setTooltip('Get a resource location variable (res:// name or a path).');
  }
};

Blockly.Blocks['pcr_get_color'] = {
  init: function () {
    this.appendDummyInput()
      .appendField('get color')
      .appendField(pcrVarDropdown('color'), 'VAR');
    this.setOutput(true, 'String');
    this.setColour(PCR_VAR_COLOURS.color);
    this.setTooltip('Get a color variable (#RRGGBB).');
  }
};

Blockly.Blocks['pcr_get_gui'] = {
  init: function () {
    this.appendDummyInput()
      .appendField('get GUI')
      .appendField(pcrVarDropdown('gui'), 'VAR');
    this.setOutput(true, 'Gui');
    this.setColour(PCR_VAR_COLOURS.gui);
    this.setTooltip('Get a gui variable (a GUI window handle).');
  }
};

Blockly.Python['pcr_get_text'] = function (block) {
  var varName = _pcrPyName(block.getFieldValue('VAR'));
  if (!varName) return ["''", Blockly.Python.ORDER_ATOMIC];
  return [varName, Blockly.Python.ORDER_ATOMIC];
};

Blockly.Python['pcr_get_number'] = function (block) {
  var varName = _pcrPyName(block.getFieldValue('VAR'));
  if (!varName) return ['0', Blockly.Python.ORDER_ATOMIC];
  return [varName, Blockly.Python.ORDER_ATOMIC];
};

Blockly.Python['pcr_get_logic'] = function (block) {
  var varName = _pcrPyName(block.getFieldValue('VAR'));
  if (!varName) return ['False', Blockly.Python.ORDER_ATOMIC];
  return [varName, Blockly.Python.ORDER_ATOMIC];
};

Blockly.Python['pcr_get_list'] = function (block) {
  var varName = _pcrPyName(block.getFieldValue('VAR'));
  if (!varName) return ['[]', Blockly.Python.ORDER_ATOMIC];
  return [varName, Blockly.Python.ORDER_ATOMIC];
};

Blockly.Python['pcr_get_image'] = function (block) {
  var varName = _pcrPyName(block.getFieldValue('VAR'));
  if (!varName) return ['None', Blockly.Python.ORDER_ATOMIC];
  return [varName, Blockly.Python.ORDER_ATOMIC];
};

Blockly.Python['pcr_get_resloc'] = function (block) {
  var varName = _pcrPyName(block.getFieldValue('VAR'));
  if (!varName) return ["''", Blockly.Python.ORDER_ATOMIC];
  return [varName, Blockly.Python.ORDER_ATOMIC];
};

Blockly.Python['pcr_get_gui'] = function (block) {
  var varName = _pcrPyName(block.getFieldValue('VAR'));
  if (!varName) return ['0', Blockly.Python.ORDER_ATOMIC];
  return [varName, Blockly.Python.ORDER_ATOMIC];
};

Blockly.Blocks['pcr_get_guiel'] = {
  init: function () {
    this.appendDummyInput()
      .appendField('get GUI element')
      .appendField(pcrVarDropdown('guiel'), 'VAR');
    this.setOutput(true, 'GuiElem');
    this.setColour(PCR_VAR_COLOURS.guiel);
    this.setTooltip('Get a gui element variable (a handle to one widget inside a GUI window).');
  }
};

Blockly.Python['pcr_get_guiel'] = function (block) {
  var varName = _pcrPyName(block.getFieldValue('VAR'));
  if (!varName) return ['guiel_new()', Blockly.Python.ORDER_ATOMIC];
  return [varName, Blockly.Python.ORDER_ATOMIC];
};

Blockly.Python['pcr_get_color'] = function (block) {
  var varName = _pcrPyName(block.getFieldValue('VAR'));
  if (!varName) return ['"#000000"', Blockly.Python.ORDER_ATOMIC];
  return [varName, Blockly.Python.ORDER_ATOMIC];
};
