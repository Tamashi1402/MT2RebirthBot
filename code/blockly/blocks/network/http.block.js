/* MacroForge network blocks — HTTP GET/POST, JSON paths (server-side, CORS-free). */
(function () {
  function num(v, d) { var n = parseFloat(v); return isNaN(n) ? d : n; }

  Blockly.Blocks['mf_http_get'] = {
    init: function () {
      this.appendValueInput('URL').setCheck('String').appendField('HTTP GET');
      this.appendValueInput('TIMEOUT').setCheck('Number').appendField('timeout');
      this.setOutput(true, null);
      this.setInputsInline(true);
      this.setColour(210);
      this.setTooltip('Fetch a URL (GET). Returns parsed JSON when the response is JSON, otherwise text. Runs server-side — no CORS limits.');
    }
  };
  Blockly.Python['mf_http_get'] = function (b) {
    var url = Blockly.Python.valueToCode(b, 'URL', Blockly.Python.ORDER_NONE) || '""';
    var t = Blockly.Python.valueToCode(b, 'TIMEOUT', Blockly.Python.ORDER_NONE) || '10';
    return ['macroforge.engine.http.get(' + url + ', ' + t + ')', Blockly.Python.ORDER_FUNCTION_CALL];
  };

  Blockly.Blocks['mf_http_post'] = {
    init: function () {
      this.appendValueInput('URL').setCheck('String').appendField('HTTP POST');
      this.appendValueInput('BODY').setCheck(null).appendField('body');
      this.appendValueInput('TIMEOUT').setCheck('Number').appendField('timeout');
      this.setOutput(true, null);
      this.setInputsInline(true);
      this.setColour(210);
      this.setTooltip('POST body (text or JSON) to a URL. Returns the parsed response.');
    }
  };
  Blockly.Python['mf_http_post'] = function (b) {
    var url = Blockly.Python.valueToCode(b, 'URL', Blockly.Python.ORDER_NONE) || '""';
    var body = Blockly.Python.valueToCode(b, 'BODY', Blockly.Python.ORDER_NONE) || 'None';
    var t = Blockly.Python.valueToCode(b, 'TIMEOUT', Blockly.Python.ORDER_NONE) || '10';
    return ['macroforge.engine.http.post(' + url + ', ' + body + ', ' + t + ')', Blockly.Python.ORDER_FUNCTION_CALL];
  };

  Blockly.Blocks['mf_http_json_get'] = {
    init: function () {
      this.appendValueInput('DATA').setCheck(null).appendField('json get');
      this.appendValueInput('PATH').setCheck('String').appendField('path');
      this.setOutput(true, null);
      this.setInputsInline(true);
      this.setColour(210);
      this.setTooltip('Read a value out of parsed JSON. Path like "user.rebirths" — lists with numeric parts "items.0.name".');
    }
  };
  Blockly.Python['mf_http_json_get'] = function (b) {
    var data = Blockly.Python.valueToCode(b, 'DATA', Blockly.Python.ORDER_NONE) || 'None';
    var path = Blockly.Python.valueToCode(b, 'PATH', Blockly.Python.ORDER_NONE) || '"data.total"';
    return ['macroforge.engine.http.json_get(' + data + ', ' + path + ')', Blockly.Python.ORDER_FUNCTION_CALL];
  };

  Blockly.Blocks['mf_http_status'] = {
    init: function () {
      this.appendValueInput('URL').setCheck('String').appendField('HTTP status of');
      this.setOutput(true, 'Number');
      this.setInputsInline(true);
      this.setColour(210);
      this.setTooltip('HTTP status code of a GET against the URL (200, 404, …).');
    }
  };
  Blockly.Python['mf_http_status'] = function (b) {
    var url = Blockly.Python.valueToCode(b, 'URL', Blockly.Python.ORDER_NONE) || '""';
    return ['macroforge.engine.http.status(' + url + ')', Blockly.Python.ORDER_FUNCTION_CALL];
  };
})();
