// ╔══════════════════════════════════════════════╗
// ║ Game blocks — MT2 game state detection         ║
// ║ is_in_menu, read_stone, health, etc.           ║
// ╚══════════════════════════════════════════════╝

// ─── Is in menu? ───
Blockly.Blocks['me_is_in_menu'] = {
  init: function() {
    this.appendDummyInput().appendField("is in menu");
    this.setOutput(true, "Boolean"); this.setColour(280);
    this.setTooltip("Check if the game is currently in the main menu");
  }
};
Blockly.Python['me_is_in_menu'] = function(b) {
  return ['screen.is_in_menu()', Blockly.Python.ORDER_FUNCTION_CALL];
};

// ─── Is rebirth screen? ───
Blockly.Blocks['me_is_rebirth_screen'] = {
  init: function() {
    this.appendDummyInput().appendField("is on rebirth screen");
    this.setOutput(true, "Boolean"); this.setColour(280);
    this.setTooltip("Check if the game is on the rebirth/upgrade screen");
  }
};
Blockly.Python['me_is_rebirth_screen'] = function(b) {
  return ['screen.is_rebirth_screen()', Blockly.Python.ORDER_FUNCTION_CALL];
};

// ─── Read stone value ───
Blockly.Blocks['me_read_stone'] = {
  init: function() {
    this.appendDummyInput().appendField("read stone value");
    this.setOutput(true, "Number"); this.setColour(280);
    this.setTooltip("Read the current stone value from the game HUD");
  }
};
Blockly.Python['me_read_stone'] = function(b) {
  return ['screen.read_stone()', Blockly.Python.ORDER_FUNCTION_CALL];
};

// ─── Rock health (red %) ───
Blockly.Blocks['me_rock_health'] = {
  init: function() {
    this.appendDummyInput().appendField("rock health (red %)");
    this.setOutput(true, "Number"); this.setColour(280);
    this.setTooltip("Get the red percentage of the rock health bar (0-100)");
  }
};
Blockly.Python['me_rock_health'] = function(b) {
  return ['screen.rock_health_red_percent()', Blockly.Python.ORDER_FUNCTION_CALL];
};

// ─── Kraken health bar visible ───
Blockly.Blocks['me_kraken_health_seen'] = {
  init: function() {
    this.appendDummyInput().appendField("kraken health bar visible");
    this.setOutput(true, "Boolean"); this.setColour(280);
    this.setTooltip("Check if the Kraken boss health bar is visible on screen");
  }
};
Blockly.Python['me_kraken_health_seen'] = function(b) {
  return ['screen.kraken_health_bar_seen()', Blockly.Python.ORDER_FUNCTION_CALL];
};

// ─── Check alive ───
Blockly.Blocks['me_check_alive'] = {
  init: function() {
    this.appendDummyInput().appendField("is alive");
    this.setOutput(true, "Boolean"); this.setColour(280);
    this.setTooltip("Check if the player character is alive");
  }
};
Blockly.Python['me_check_alive'] = function(b) {
  return ['bot._check_alive()', Blockly.Python.ORDER_FUNCTION_CALL];
};

// ─── Get run time ───
Blockly.Blocks['me_get_run_time'] = {
  init: function() {
    this.appendDummyInput().appendField("run time (seconds)");
    this.setOutput(true, "Number"); this.setColour(280);
    this.setTooltip("Get elapsed time since the bot run started (seconds)");
  }
};
Blockly.Python['me_get_run_time'] = function(b) {
  return ['bot._get_run_elapsed()', Blockly.Python.ORDER_FUNCTION_CALL];
};

// ─── Is area 5 unlocked? ───
Blockly.Blocks['me_is_area5_unlocked'] = {
  init: function() {
    this.appendDummyInput().appendField("area 5 unlocked");
    this.setOutput(true, "Boolean"); this.setColour(280);
    this.setTooltip("Check if area 5 has been unlocked");
  }
};
Blockly.Python['me_is_area5_unlocked'] = function(b) {
  return ['bot._is_area5_unlocked()', Blockly.Python.ORDER_FUNCTION_CALL];
};

// ─── Read crater timer ───
Blockly.Blocks['me_read_crater_timer'] = {
  init: function() {
    this.appendDummyInput().appendField("crater timer (seconds)");
    this.setOutput(true, "Number"); this.setColour(280);
    this.setTooltip("Read the crater mode timer from the game screen");
  }
};
Blockly.Python['me_read_crater_timer'] = function(b) {
  return ['screen.read_crater_timer()', Blockly.Python.ORDER_FUNCTION_CALL];
};

// ─── Grab screen region ───
Blockly.Blocks['me_grab_region'] = {
  init: function() {
    this.appendValueInput("X").setCheck("Number").appendField("grab screen region x");
    this.appendValueInput("Y").setCheck("Number").appendField("y");
    this.appendValueInput("W").setCheck("Number").appendField("width");
    this.appendValueInput("H").setCheck("Number").appendField("height");
    this.setInputsInline(true);
    this.setOutput(true, null); this.setColour(280);
    this.setTooltip("Capture a screen region as an image object");
  }
};
Blockly.Python['me_grab_region'] = function(b) {
  var x = Blockly.Python.valueToCode(b, 'X', Blockly.Python.ORDER_NONE) || '0';
  var y = Blockly.Python.valueToCode(b, 'Y', Blockly.Python.ORDER_NONE) || '0';
  var w = Blockly.Python.valueToCode(b, 'W', Blockly.Python.ORDER_NONE) || '0';
  var h = Blockly.Python.valueToCode(b, 'H', Blockly.Python.ORDER_NONE) || '0';
  return ['screen.grab_region((' + x + ', ' + y + ', ' + w + ', ' + h + '))', Blockly.Python.ORDER_FUNCTION_CALL];
};

// ─── Grab full screen ───
Blockly.Blocks['me_grab_full_screen'] = {
  init: function() {
    this.appendDummyInput().appendField("grab full screen");
    this.setOutput(true, null); this.setColour(280);
    this.setTooltip("Capture the entire screen as an image object");
  }
};
Blockly.Python['me_grab_full_screen'] = function(b) {
  return ['screen.grab_full_screen()', Blockly.Python.ORDER_FUNCTION_CALL];
};

// ─── Color match percent ───
Blockly.Blocks['me_color_match'] = {
  init: function() {
    this.appendValueInput("IMG").appendField("color match % in image");
    this.appendValueInput("HUE").setCheck("Number").appendField("hue");
    this.appendValueInput("SAT").setCheck("Number").appendField("sat");
    this.appendValueInput("VAL").setCheck("Number").appendField("val");
    this.setInputsInline(true);
    this.setOutput(true, "Number"); this.setColour(280);
    this.setTooltip("Get percentage of pixels matching a target HSV color");
  }
};
Blockly.Python['me_color_match'] = function(b) {
  var img = Blockly.Python.valueToCode(b, 'IMG', Blockly.Python.ORDER_NONE) || 'None';
  var hue = Blockly.Python.valueToCode(b, 'HUE', Blockly.Python.ORDER_NONE) || '0';
  var sat = Blockly.Python.valueToCode(b, 'SAT', Blockly.Python.ORDER_NONE) || '0';
  var val = Blockly.Python.valueToCode(b, 'VAL', Blockly.Python.ORDER_NONE) || '0';
  return ['screen.color_match_percent(' + img + ', (' + hue + ', ' + sat + ', ' + val + '))', Blockly.Python.ORDER_FUNCTION_CALL];
};
