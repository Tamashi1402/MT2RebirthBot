// ╔══════════════════════════════════════════════╗
// ║ System blocks — clipboard, commands, etc       ║
// ║ Ported from MacroEngine, adapted for MT2 bot   ║
// ╚══════════════════════════════════════════════╝

// ─── Run command ───
Blockly.Blocks['me_run_command'] = {
  init: function() {
    this.appendValueInput("COMMAND").setCheck("String").appendField("run command");
    this.setPreviousStatement(true, null); this.setNextStatement(true, null);
    this.setColour(260); this.setTooltip("Run a system shell command");
  }
};
Blockly.Python['me_run_command'] = function(b) {
  var cmd = Blockly.Python.valueToCode(b, 'COMMAND', Blockly.Python.ORDER_NONE) || "''";
  return 'import subprocess; subprocess.Popen(' + cmd + ', shell=True)\n';
};

// ─── Run command and get output ───
Blockly.Blocks['me_run_command_output'] = {
  init: function() {
    this.appendValueInput("COMMAND").setCheck("String").appendField("run and get output");
    this.setOutput(true, "String"); this.setColour(160);
    this.setTooltip("Run a command and return its stdout output");
  }
};
Blockly.Python['me_run_command_output'] = function(b) {
  var cmd = Blockly.Python.valueToCode(b, 'COMMAND', Blockly.Python.ORDER_NONE) || "''";
  return ['import subprocess; subprocess.check_output(' + cmd + ', shell=True).decode().strip()', Blockly.Python.ORDER_FUNCTION_CALL];
};

// ─── Clipboard get ───
Blockly.Blocks['me_clipboard_get'] = {
  init: function() {
    this.appendDummyInput().appendField("clipboard get");
    this.setOutput(true, "String"); this.setColour(160);
    this.setTooltip("Get the current clipboard text");
  }
};
Blockly.Python['me_clipboard_get'] = function(b) {
  return ['import pyperclip; pyperclip.paste()', Blockly.Python.ORDER_FUNCTION_CALL];
};

// ─── Clipboard set ───
Blockly.Blocks['me_clipboard_set'] = {
  init: function() {
    this.appendValueInput("TEXT").setCheck("String").appendField("clipboard set");
    this.setPreviousStatement(true, null); this.setNextStatement(true, null);
    this.setColour(260); this.setTooltip("Set the clipboard text");
  }
};
Blockly.Python['me_clipboard_set'] = function(b) {
  var text = Blockly.Python.valueToCode(b, 'TEXT', Blockly.Python.ORDER_NONE) || "''";
  return 'import pyperclip; pyperclip.copy(' + text + ')\n';
};

// ─── Open URL ───
Blockly.Blocks['me_open_url'] = {
  init: function() {
    this.appendValueInput("URL").setCheck("String").appendField("open url");
    this.setPreviousStatement(true, null); this.setNextStatement(true, null);
    this.setColour(260); this.setTooltip("Open a URL in the default web browser");
  }
};
Blockly.Python['me_open_url'] = function(b) {
  var url = Blockly.Python.valueToCode(b, 'URL', Blockly.Python.ORDER_NONE) || "''";
  return 'import webbrowser; webbrowser.open(' + url + ')\n';
};

// ─── Notification ───
Blockly.Blocks['me_notification'] = {
  init: function() {
    this.appendValueInput("TITLE").setCheck("String").appendField("notify title");
    this.appendValueInput("MESSAGE").setCheck("String").appendField("message");
    this.setInputsInline(true);
    this.setPreviousStatement(true, null); this.setNextStatement(true, null);
    this.setColour(260); this.setTooltip("Show a desktop notification");
  }
};
Blockly.Python['me_notification'] = function(b) {
  var title = Blockly.Python.valueToCode(b, 'TITLE', Blockly.Python.ORDER_NONE) || "''";
  var msg = Blockly.Python.valueToCode(b, 'MESSAGE', Blockly.Python.ORDER_NONE) || "''";
  return 'import ctypes; ctypes.windll.user32.MessageBoxW(0, str(' + msg + '), str(' + title + '), 0x40)\n';
};

// ─── Get focused window ───
Blockly.Blocks['me_get_focused_window'] = {
  init: function() {
    this.appendDummyInput().appendField("get focused window");
    this.setOutput(true, "String"); this.setColour(160);
    this.setTooltip("Get the title of the currently focused (foreground) window");
  }
};
Blockly.Python['me_get_focused_window'] = function(b) {
  return ['import ctypes; ctypes.windll.user32.GetWindowTextW(ctypes.windll.user32.GetForegroundWindow())', Blockly.Python.ORDER_FUNCTION_CALL];
};

// ─── Is window focused ───
Blockly.Blocks['me_is_window_focused'] = {
  init: function() {
    this.appendValueInput("TITLE").setCheck("String").appendField("is window focused");
    this.setOutput(true, "Boolean"); this.setColour(210);
    this.setTooltip("Check if a window with the given title is currently in the foreground");
  }
};
Blockly.Python['me_is_window_focused'] = function(b) {
  var title = Blockly.Python.valueToCode(b, 'TITLE', Blockly.Python.ORDER_NONE) || "''";
  return ['import ctypes; ctypes.windll.user32.GetWindowTextW(ctypes.windll.user32.GetForegroundWindow()) == str(' + title + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};
