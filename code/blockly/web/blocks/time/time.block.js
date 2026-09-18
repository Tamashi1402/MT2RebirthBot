// ╔══════════════════════════════════════════════╗
// ║ Time blocks — sleep, timestamps, timers        ║
// ║ Ported 100% from PyCreator                     ║
// ╚══════════════════════════════════════════════╝

// ─── Sleep (delay) ───
Blockly.Blocks['me_sleep'] = {
  init: function() {
    this.appendValueInput("SECONDS").setCheck("Number").appendField("sleep (seconds)");
    this.setPreviousStatement(true, null); this.setNextStatement(true, null);
    this.setColour(90); this.setTooltip("Pause execution for a number of seconds");
  }
};
Blockly.Python['me_sleep'] = function(b) {
  var s = Blockly.Python.valueToCode(b, 'SECONDS', Blockly.Python.ORDER_NONE) || '0';
  return 'time.sleep(' + s + ')\n';
};

// ─── Delay in ms ───
Blockly.Blocks['me_delay_ms'] = {
  init: function() {
    this.appendValueInput("MS").setCheck("Number").appendField("delay (ms)");
    this.setPreviousStatement(true, null); this.setNextStatement(true, null);
    this.setColour(90); this.setTooltip("Pause execution for a number of milliseconds");
  }
};
Blockly.Python['me_delay_ms'] = function(b) {
  var ms = Blockly.Python.valueToCode(b, 'MS', Blockly.Python.ORDER_NONE) || '0';
  return 'time.sleep(float(' + ms + ') / 1000.0)\n';
};

// ─── Time now (string) ───
Blockly.Blocks['me_time_now'] = {
  init: function() {
    this.appendDummyInput().appendField("time now");
    this.setOutput(true, "String"); this.setColour(160);
    this.setTooltip("Get the current time as a formatted string");
  }
};
Blockly.Python['me_time_now'] = function(b) {
  return ['time.strftime("%H:%M:%S")', Blockly.Python.ORDER_FUNCTION_CALL];
};

// ─── Date now (string) ───
Blockly.Blocks['me_date_now'] = {
  init: function() {
    this.appendDummyInput().appendField("date now");
    this.setOutput(true, "String"); this.setColour(160);
    this.setTooltip("Get the current date as a formatted string");
  }
};
Blockly.Python['me_date_now'] = function(b) {
  return ['time.strftime("%Y-%m-%d")', Blockly.Python.ORDER_FUNCTION_CALL];
};

// ─── Timestamp (epoch) ───
Blockly.Blocks['me_timestamp'] = {
  init: function() {
    this.appendDummyInput().appendField("timestamp");
    this.setOutput(true, "Number"); this.setColour(230);
    this.setTooltip("Get the current Unix timestamp (seconds since epoch)");
  }
};
Blockly.Python['me_timestamp'] = function(b) {
  return ['time.time()', Blockly.Python.ORDER_FUNCTION_CALL];
};

// ─── Timer (elapsed since start) ───
Blockly.Blocks['me_timer'] = {
  init: function() {
    this.appendDummyInput().appendField(new Blockly.FieldDropdown([
      ["start timer", "start"], ["read timer (seconds)", "read"], ["read timer (ms)", "read_ms"]
    ]), "ACTION");
    this.setPreviousStatement(true, null); this.setNextStatement(true, null);
    this.setOutput(true, null); this.setColour(230);
    this.setTooltip("Start or read a high-precision timer");
  }
};
Blockly.Python['me_timer'] = function(b) {
  var action = b.getFieldValue('ACTION');
  if (action === 'start') { return 'engine.time_api.timer_start()\n'; }
  if (action === 'read_ms') { return ['engine.time_api.timer_read_ms()', Blockly.Python.ORDER_FUNCTION_CALL]; }
  return ['engine.time_api.timer_read()', Blockly.Python.ORDER_FUNCTION_CALL];
};

// ─── Time parts ───
Blockly.Blocks['me_time_parts'] = {
  init: function() {
    this.appendDummyInput().appendField("current").appendField(new Blockly.FieldDropdown([
      ["hour", "hour"], ["minute", "minute"], ["second", "second"],
      ["day", "day"], ["month", "month"], ["year", "year"], ["weekday", "weekday"]
    ]), "PART");
    this.setOutput(true, "Number"); this.setColour(230);
    this.setTooltip("Get a specific part of the current date/time");
  }
};
Blockly.Python['me_time_parts'] = function(b) {
  var part = b.getFieldValue('PART');
  var mapping = {hour:8, minute:9, second:10, day:6, month:5, year:7, weekday:11};
  var idx = mapping[part] || 0;
  return ['int(time.localtime()[' + idx + '])', Blockly.Python.ORDER_INDEX];
};

// ─── Time format ───
Blockly.Blocks['me_time_format'] = {
  init: function() {
    this.appendValueInput("FORMAT").setCheck("String").appendField("format time");
    this.setOutput(true, "String"); this.setColour(160);
    this.setTooltip("Format the current time using a strftime format string");
  }
};
Blockly.Python['me_time_format'] = function(b) {
  var fmt = Blockly.Python.valueToCode(b, 'FORMAT', Blockly.Python.ORDER_NONE) || "'%H:%M:%S'";
  return ['time.strftime(' + fmt + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};

// ─── Time parse ───
Blockly.Blocks['me_time_parse'] = {
  init: function() {
    this.appendValueInput("TIME_STR").setCheck("String").appendField("parse time");
    this.appendValueInput("FORMAT").setCheck("String").appendField("format");
    this.setInputsInline(true);
    this.setOutput(true, "Number"); this.setColour(230);
    this.setTooltip("Parse a time string into a timestamp");
  }
};
Blockly.Python['me_time_parse'] = function(b) {
  var ts = Blockly.Python.valueToCode(b, 'TIME_STR', Blockly.Python.ORDER_NONE) || "''";
  var fmt = Blockly.Python.valueToCode(b, 'FORMAT', Blockly.Python.ORDER_NONE) || "'%Y-%m-%d'";
  return ['time.mktime(time.strptime(' + ts + ', ' + fmt + '))', Blockly.Python.ORDER_FUNCTION_CALL];
};
