// Macro Engine - no-preset edition
// Supports: open any .macro, save in place, save-as, import into macros/

const supportedBlocks = [
  'LABEL','GOTO','DELAY',
  'KEY_DOWN','KEY_UP','KEY_PRESS',
  'MOUSE_MOVE_ABS','MOUSE_LEFT_DOWN','MOUSE_LEFT_UP','MOUSE_LEFT_CLICK',
  'MOUSE_REL','SMOOTH_MOVE',
  'REPEAT','ENDREPEAT',
  'VARIABLE','SET_VARIABLE','IMAGE',
  'IF','ELSE_IF','END_IF',
  'PLAY_MACRO',
];

const blockDefaults = {
  LABEL:            'START',
  GOTO:             'START',
  DELAY:            '100',
  KEY_DOWN:         '0x57',
  KEY_UP:           '0x57',
  KEY_PRESS:        '0x46',
  MOUSE_MOVE_ABS:   '960,540',
  MOUSE_LEFT_DOWN:  '',
  MOUSE_LEFT_UP:    '',
  MOUSE_LEFT_CLICK: '',
  MOUSE_REL:        '10,0',
  SMOOTH_MOVE:      '60,0',
  REPEAT:           '2',
  ENDREPEAT:        '',
  VARIABLE:         '{"name":"var1","var_type":"number","value":0}',
  SET_VARIABLE:     '{"name":"var1","op":"set","value":0}',
  IMAGE:            '{"var":"image_found","path":"","threshold":85,"fixed":true,"base_w":1920,"base_h":1080,"x1":0,"y1":0,"x2":100,"y2":100,"search_x1":0,"search_y1":0,"search_x2":1920,"search_y2":1080}',
  IF:               '{"mode":"boolean","name":"image_found","value":true}',
  ELSE_IF:          '{"mode":"boolean","name":"image_found","value":true}',
  END_IF:           '',
  PLAY_MACRO:       '',
};

const valueLessBlocks = new Set([
  'ENDREPEAT',
  'MOUSE_LEFT_DOWN',
  'MOUSE_LEFT_UP',
  'MOUSE_LEFT_CLICK',
  'END_IF',
]);

const keyOptions = [
  ['A','0x41'],['B','0x42'],['C','0x43'],['D','0x44'],['E','0x45'],['F','0x46'],
  ['G','0x47'],['H','0x48'],['I','0x49'],['J','0x4A'],['K','0x4B'],['L','0x4C'],
  ['M','0x4D'],['N','0x4E'],['O','0x4F'],['P','0x50'],['Q','0x51'],['R','0x52'],
  ['S','0x53'],['T','0x54'],['U','0x55'],['V','0x56'],['W','0x57'],['X','0x58'],
  ['Y','0x59'],['Z','0x5A'],
  ['0','0x30'],['1','0x31'],['2','0x32'],['3','0x33'],['4','0x34'],
  ['5','0x35'],['6','0x36'],['7','0x37'],['8','0x38'],['9','0x39'],
  ['F1','0x70'],['F2','0x71'],['F3','0x72'],['F4','0x73'],['F5','0x74'],
  ['F6','0x75'],['F7','0x76'],['F8','0x77'],['F9','0x78'],['F10','0x79'],
  ['F11','0x7A'],['F12','0x7B'],
  ['Space','0x20'],['Enter','0x0D'],['Tab','0x09'],['Escape','0x1B'],
  ['Backspace','0x08'],['Delete','0x2E'],
  ['Left Arrow','0x25'],['Up Arrow','0x26'],['Right Arrow','0x27'],['Down Arrow','0x28'],
  ['Home','0x24'],['End','0x23'],['Page Up','0x21'],['Page Down','0x22'],
  ['Left Ctrl','0xA2'],['Right Ctrl','0xA3'],['Ctrl (generic)','0x11'],
  ['Left Shift','0xA0'],['Right Shift','0xA1'],['Shift (generic)','0x10'],
  ['Left Alt','0xA4'],['Right Alt','0xA5'],['Alt (generic)','0x12'],
];

const bindingOptions = [
  ['F1','F1'],['F2','F2'],['F3','F3'],['F4','F4'],['F5','F5'],['F6','F6'],
  ['F7','F7'],['F8','F8'],['F9','F9'],['F10','F10'],['F11','F11'],['F12','F12'],
  ['A','A'],['B','B'],['C','C'],['D','D'],['E','E'],['F','F'],['G','G'],['H','H'],
  ['I','I'],['J','J'],['K','K'],['L','L'],['M','M'],['N','N'],['O','O'],['P','P'],
  ['Q','Q'],['R','R'],['S','S'],['T','T'],['U','U'],['V','V'],['W','W'],['X','X'],
  ['Y','Y'],['Z','Z'],['Space','SPACE'],
];

const pickerGroups = {
  mouse: {
    title: 'Mouse',
    options: [
      ['SMOOTH_MOVE', 'Smooth Move', 'Sensitivity-scaled relative mouse movement (in-game).'],
      ['MOUSE_MOVE_ABS', 'Absolute Move', 'Move cursor to x,y screen position (GUI).'],
      ['MOUSE_LEFT_CLICK', 'Left Click', 'Press and release left mouse.'],
      ['MOUSE_LEFT_DOWN', 'Left Hold', 'Hold left mouse down.'],
      ['MOUSE_LEFT_UP', 'Left Release', 'Release left mouse.'],
    ],
  },
  keyboard: {
    title: 'Keyboard',
    options: [
      ['KEY_PRESS', 'Key Press', 'Press and release a key.'],
      ['KEY_DOWN', 'Key Hold', 'Hold a key down.'],
      ['KEY_UP', 'Key Release', 'Release a held key.'],
    ],
  },
  logic: {
    title: 'Logic',
    options: [
      ['VARIABLE', 'Variable', 'Create a number or boolean variable.'],
      ['SET_VARIABLE', 'Set Variable', 'Set, add, subtract, or toggle a variable.'],
      ['IMAGE', 'Image', 'Capture a region and set a boolean variable from match percent.'],
      ['IF', 'If', 'Run following blocks when a variable condition is true.'],
      ['ELSE_IF', 'Else If', 'Alternative condition for the same IF chain.'],
      ['END_IF', 'End If', 'Close the current IF chain.'],
    ],
  },
};

const MACRO_FOLDER_LABELS = {
  '': 'Root',
  'teleports': 'Teleports',
  'engine': 'Engine',
  'rebirth_mode': 'Rebirth',
  'rebirth_mode/area1': 'Rebirth / Area 1',
  'rebirth_mode/area2': 'Rebirth / Area 2',
  'rebirth_mode/area3': 'Rebirth / Area 3',
  'rebirth_mode/area4': 'Rebirth / Area 4',
  'rebirth_mode/area5': 'Rebirth / Area 5',
  'delve_mode': 'Delve',
  'kraken_mode': 'Kraken',
  'zytos_mode': 'Zytos',
  'crater_mode': 'Crater',
  'meteor_mode': 'Meteor',
};
const MACRO_FOLDER_ORDER = [
  'rebirth_mode',
  'rebirth_mode/area1', 'rebirth_mode/area2', 'rebirth_mode/area3',
  'rebirth_mode/area4', 'rebirth_mode/area5',
  'delve_mode', 'kraken_mode', 'zytos_mode', 'crater_mode',
  'meteor_mode',
  'teleports', 'engine', '',
];
const MACRO_HINTS = {
  base_to_baserock: 'Start after teleporting to base. Walk to baserock and stop when you are facing it in hitting radius. Do not start hitting.',
  base_to_meteor_shortcut_p1: 'Start after teleporting to base. Walk through the base portal into Area 6 and stop after you have spawned in Area 6.',
  base_to_meteor_shortcut_p1_shortcut: 'Start from the end position of base_to_baserock (facing baserock). Walk through the base portal into Area 6 and stop after you have spawned in Area 6.',
  base_to_meteor_shortcut_p3: 'Start after teleporting to Area 5. Walk to the Area 5 Stage 3 meteor and stop when it is in hitting radius. Do not start hitting.',
  base_to_rebirth: 'Start after teleporting to base. Walk to the rebirth NPC and press E until the rebirth menu is open, then STOP recording.\n\nDo not click Rebirth / Confirm with the mouse while recording — UI clicks are not sensitivity-scaled. After saving, open the .macro in Notepad and paste this on the end:\n\nDELAY:1000\nMOUSE_MOVE_ABS:959,937\nDELAY:500\nMOUSE_LEFT_CLICK\nDELAY:1000\nMOUSE_MOVE_ABS:1544,936\nDELAY:500\nMOUSE_LEFT_CLICK\nDELAY:5000',
  unlock_drills: 'Start after teleporting to base. Walk to the drill NPC, press E to open the shop, then STOP recording.\n\nShop buttons are UI — after saving, keep/add these absolute clicks (1920x1080):\nMOUSE_MOVE_ABS:1045,858 + click (unlock)\nMOUSE_MOVE_ABS:660,953 + click (close/back)',
  area1_to_bramble: 'Start after teleporting to Area 1 (on the pad). Walk to the Bramble NPC and stop in interact range. Do not open the boss menu (fight_bramble_open does that).',
  fight_bramble_open: 'Start standing at the Bramble NPC (end of area1_to_bramble). Walk in, press E to open the Bramble info card, and stop when the card is open. Do not click JOIN.',
  fight_bramble_join: 'Do not record mouse turns. This is UI-only (JOIN button).\n\nIf JOIN misses, edit the file and keep absolute clicks (1920x1080):\nMOUSE_MOVE_ABS:1337,830\nDELAY:200\nMOUSE_LEFT_CLICK\nDELAY:1000\nMOUSE_LEFT_CLICK\nDELAY:2000\n\nDo not click a loadout slot here — loadouts are selected by the bot.',
  fight_bramble: 'Legacy combined walk + open + JOIN. Prefer area1_to_bramble + fight_bramble_open + fight_bramble_join. If you re-record this one: start at Area 1 pad, walk to Bramble, open the card, then stop before JOIN and paste the fight_bramble_join UI clicks.',
  area1_to_meteor: 'Start after teleporting to Area 1 (on the pad). Walk to the Area 1 meteor and stop when it is in hitting radius. Do not start hitting.',
  area5_to_meteor: 'Start after teleporting to Area 5 (on the pad). Walk to the Area 5 meteor and stop when it is in hitting radius. Do not start hitting.',
  area5_to_delve: 'Start after teleporting to Area 5 (on the pad). Walk to the Delve entrance, press E to open the Delve card, and stop when the card is open. Do not click Join — the bot clicks that.',
  area7_to_kraken: 'Start after teleporting to Area 7 (on the pad). Walk to Kraken, press E to open the Kraken card, and stop when the card is open. Do not click Join — the bot clicks that.',
  a8_to_zytos: 'Start after teleporting to Area 8 (on the pad). Walk to Zytos and stop in interact range / facing the Zytos card. Do not click Join — the bot clicks that.',
  cosmic_to_crater: 'Start after teleporting to Cosmic. Walk to the Crater entrance and stop when you can join. Do not click Join — the bot handles Crater join.',
  area6_to_node: 'Meteor (Area 6). Start after teleporting to Area 6 (on the pad). Walk to the rock node and stop when you are facing it in hitting radius. Do not start hitting. The bot holds left click for 1 second to break it.',
  area6_to_meteor: 'Meteor (Area 6). Start after teleporting to Area 6 (on the pad). Walk to the Area 6 meteor and stop when it is in hitting radius. Do not start hitting.',
  base_to_area6: 'Start after teleporting to base. Walk through the base portal into Area 6 and stop after you have spawned in Area 6 (unlocks F4 Area 6).',
  area6_to_stage1: 'Start after teleporting to Area 6 (on the pad). Walk to the Area 6 Stage 1 rock and stop when you are facing it in hitting radius. Do not start hitting.',
  area6_to_stage2: 'Start after teleporting to Area 6 (on the pad). Walk to the Area 6 Stage 2 rock and stop when you are facing it in hitting radius. Do not start hitting.',
  area6_to_stage3: 'Start after teleporting to Area 6 (on the pad). Walk to the Area 6 Stage 3 rock and stop when you are facing it in hitting radius. Do not start hitting.',
  area6_to_stage4: 'Start after teleporting to Area 6 (on the pad). Walk to the Area 6 Stage 4 rock and stop when you are facing it in hitting radius. Do not start hitting.',
  area7_to_meteor: 'Meteor (Area 7). Start after teleporting to Area 7 (on the pad). Walk to the Area 7 meteor and stop when it is in hitting radius. Do not start hitting.',
  area8_to_meteor: 'Meteor (Area 8). Start after teleporting to Area 8 (on the pad). Walk to the Area 8 meteor and stop when it is in hitting radius. Do not start hitting.',
};
for (let area = 1; area <= 5; area++) {
  MACRO_HINTS[`base_to_a${area}_teleport`] =
    `Start after teleporting to base. Walk through the portal into Area ${area} and stop after you have spawned in Area ${area} (unlocks teleport_to_area${area}).`;
  for (let stage = 1; stage <= 4; stage++) {
    MACRO_HINTS[`area${area}_to_stage${stage}_rock`] =
      `Start after teleporting to Area ${area} (on the pad). Walk to Stage ${stage} rock 1 and stop when you are facing it in hitting radius. Do not start hitting.`;
  }
}

let recordBindingValue = 'F5';
let playBindingValue = 'F6';
let smoothMoveBindingValue = 'L';
let lastSmoothMoveSeq = 0;

// ── DOM refs ─────────────────────────────────────────────────────────────────
const macroQuickSelect = document.getElementById('macroQuickSelect');
const macroHintBtn     = document.getElementById('macroHintBtn');
const macroHintPop     = document.getElementById('macroHintPop');
const newBtn           = document.getElementById('newBtn');
const openBtn          = document.getElementById('openBtn');
const importBtn        = document.getElementById('importBtn');
const saveBtn          = document.getElementById('saveBtn');
const saveAsBtn        = document.getElementById('saveAsBtn');
const pickerToolBtn    = document.getElementById('pickerToolBtn');
const menuWraps        = document.querySelectorAll('.menu-wrap');
const macroTopLabel    = document.getElementById('macroTopLabel');

const categoryButtons  = document.querySelectorAll('.block-category');
const blockPickerModal = document.getElementById('blockPickerModal');
const blockPickerTitle = document.getElementById('blockPickerTitle');
const blockPickerOptions = document.getElementById('blockPickerOptions');
const blockPickerClose = document.getElementById('blockPickerClose');
const cmdModal         = document.getElementById('cmdModal');
const cmdTitle         = document.getElementById('cmdTitle');
const cmdHint          = document.getElementById('cmdHint');
const cmdEventType     = document.getElementById('cmdEventType');
const cmdMouseFields   = document.getElementById('cmdMouseFields');
const cmdKeyFields     = document.getElementById('cmdKeyFields');
const cmdX             = document.getElementById('cmdX');
const cmdY             = document.getElementById('cmdY');
const cmdF2Hint        = document.getElementById('cmdF2Hint');
const cmdKey           = document.getElementById('cmdKey');
const cmdOk            = document.getElementById('cmdOk');
const cmdCancel        = document.getElementById('cmdCancel');
const cmdClose         = document.getElementById('cmdClose');
const cmdEventWrap     = document.getElementById('cmdEventWrap');
const cmdSimpleFields  = document.getElementById('cmdSimpleFields');
const cmdSimple        = document.getElementById('cmdSimple');
const cmdSimpleName    = document.getElementById('cmdSimpleName');
const cmdPlayFields    = document.getElementById('cmdPlayFields');
const cmdPlayPath      = document.getElementById('cmdPlayPath');
const cmdPlayBrowse    = document.getElementById('cmdPlayBrowse');
const cmdVarFields     = document.getElementById('cmdVarFields');
const cmdVarName       = document.getElementById('cmdVarName');
const cmdVarType       = document.getElementById('cmdVarType');
const cmdVarValueWrap  = document.getElementById('cmdVarValueWrap');
const cmdVarValue      = document.getElementById('cmdVarValue');
const cmdVarBoolWrap   = document.getElementById('cmdVarBoolWrap');
const cmdVarBool       = document.getElementById('cmdVarBool');
const cmdSetFields     = document.getElementById('cmdSetFields');
const cmdSetName       = document.getElementById('cmdSetName');
const cmdSetOp         = document.getElementById('cmdSetOp');
const cmdSetValueWrap  = document.getElementById('cmdSetValueWrap');
const cmdSetValue      = document.getElementById('cmdSetValue');
const cmdIfFields      = document.getElementById('cmdIfFields');
const cmdIfName        = document.getElementById('cmdIfName');
const cmdIfMode        = document.getElementById('cmdIfMode');
const cmdIfBoolWrap    = document.getElementById('cmdIfBoolWrap');
const cmdIfBool        = document.getElementById('cmdIfBool');
const cmdIfNumWrap     = document.getElementById('cmdIfNumWrap');
const cmdIfOp          = document.getElementById('cmdIfOp');
const cmdIfValue       = document.getElementById('cmdIfValue');
const sidebar          = document.getElementById('left-sidebar');
const sidebarToggle    = document.getElementById('sb-toggle-btn');
const blocksDiv        = document.getElementById('blocks');

const recordBtnTop     = document.getElementById('recordBtnTop');
const playStopBtn      = document.getElementById('playStopBtn');

const settingsBtn      = document.getElementById('settingsBtn');
const settingsPanel    = document.getElementById('settingsPanel');
const settingsClose    = document.getElementById('settingsClose');
const settingsCloseBottom = document.getElementById('settingsCloseBottom');
const settingsSave     = document.getElementById('settingsSave');

const saveAsModal      = document.getElementById('saveAsModal');
const saveAsPath       = document.getElementById('saveAsPath');
const saveAsName       = document.getElementById('saveAsName');
const saveAsConfirm    = document.getElementById('saveAsConfirm');
const saveAsCancel     = document.getElementById('saveAsCancel');

const fileBrowserModal   = document.getElementById('fileBrowserModal');
const fileBrowserHead    = document.getElementById('fileBrowserHead');
const fileBrowserUp      = document.getElementById('fileBrowserUp');
const fileBrowserPath    = document.getElementById('fileBrowserPath');
const fileBrowserGo      = document.getElementById('fileBrowserGo');
const fileBrowserRoots   = document.getElementById('fileBrowserRoots');
const fileBrowserEntries = document.getElementById('fileBrowserEntries');
const fileBrowserNameWrap = document.getElementById('fileBrowserNameWrap');
const fileBrowserName    = document.getElementById('fileBrowserName');
const fileBrowserStatus  = document.getElementById('fileBrowserStatus');
const fileBrowserConfirm = document.getElementById('fileBrowserConfirm');
const fileBrowserCancel  = document.getElementById('fileBrowserCancel');

const pointPickerModal = document.getElementById('pointPickerModal');
const pointPickerStart = document.getElementById('pointPickerStart');
const pointPickerResult = document.getElementById('pointPickerResult');
const pointPickerStatus = document.getElementById('pointPickerStatus');
const pointPickerClose = document.getElementById('pointPickerClose');
const pointPickerCancel = document.getElementById('pointPickerCancel');
const pointPickerCopy = document.getElementById('pointPickerCopy');

const smoothMoveModal   = document.getElementById('smoothMoveModal');
const smoothMoveResult  = document.getElementById('smoothMoveResult');
const smoothMoveStatus  = document.getElementById('smoothMoveStatus');
const smoothMoveClose   = document.getElementById('smoothMoveClose');
const smoothMoveCancel  = document.getElementById('smoothMoveCancel');
const smoothMoveCopy    = document.getElementById('smoothMoveCopy');
const smoothMoveBinding = document.getElementById('smoothMoveBinding');

const imageEditorModal = document.getElementById('imageEditorModal');
const imageEditorClose = document.getElementById('imageEditorClose');
const imageVarInput = document.getElementById('imageVarInput');
const imageResultMode = document.getElementById('imageResultMode');
const imageXVarInput = document.getElementById('imageXVarInput');
const imageYVarInput = document.getElementById('imageYVarInput');
const imageThresholdInput = document.getElementById('imageThresholdInput');
const imageFixedInput = document.getElementById('imageFixedInput');
const imagePathInput = document.getElementById('imagePathInput');
const imagePathList = document.getElementById('imagePathList');
const imagePathSelect = document.getElementById('imagePathSelect');
const imageSelectSample = document.getElementById('imageSelectSample');
const imageSelectSearch = document.getElementById('imageSelectSearch');
const imageTestCurrent = document.getElementById('imageTestCurrent');
const imageX1 = document.getElementById('imageX1');
const imageY1 = document.getElementById('imageY1');
const imageX2 = document.getElementById('imageX2');
const imageY2 = document.getElementById('imageY2');
const imageSearchX1 = document.getElementById('imageSearchX1');
const imageSearchY1 = document.getElementById('imageSearchY1');
const imageSearchX2 = document.getElementById('imageSearchX2');
const imageSearchY2 = document.getElementById('imageSearchY2');
const imageShotStatus = document.getElementById('imageShotStatus');
const imageShotWrap = document.getElementById('imageShotWrap');
const imageShotCanvas = document.getElementById('imageShotCanvas');
const imageApplySelection = document.getElementById('imageApplySelection');
const imageEditorSave = document.getElementById('imageEditorSave');
const imageEditorCancel = document.getElementById('imageEditorCancel');

const modalBackdrop    = document.getElementById('modalBackdrop');

const progressBar      = { style: {}, className: '' };
const macroLabel       = { textContent: '' };
const timeLabel        = { textContent: '' };

const sensRh = document.getElementById('sensRh');
const sensRv = document.getElementById('sensRv');
const sensUh = document.getElementById('sensUh');
const sensUv = document.getElementById('sensUv');
const sensRhSlider = document.getElementById('sensRhSlider');
const sensRvSlider = document.getElementById('sensRvSlider');
const sensUhSlider = document.getElementById('sensUhSlider');
const sensUvSlider = document.getElementById('sensUvSlider');
const recordBinding = document.getElementById('recordBinding');
const playBinding = document.getElementById('playBinding');
const playModeSelect = document.getElementById('playModeSelect');
const playModeTimes  = document.getElementById('playModeTimes');

// ── State ─────────────────────────────────────────────────────────────────────
let macroList     = [];   // [{name, path}]
let currentPath   = '';
let currentMacro  = '';
let currentMeta   = {};
let blocks        = [];
let running       = false;
let recording     = false;
let lastRecordVersion = 0;
let browserMode   = 'open';
let browserDir    = '';
let browserParent = '';
let browserFile   = '';
let autosaveTimer = null;
let isSaving      = false;
let playbackRepeatValue = 1;
let playbackTimesValue = 5;
let playbackMode = 'once';
let appUserSensitivity = { SENS_USER_H: 17, SENS_USER_V: 17 };
let renderScheduled = false;
let recorderTabArmed = !window.frameElement;
let recordBusy = false;
let playBusy = false;
let pointPickerSession = 0;
let pointPickerListening = false;
let cmdPickerSession = 0;
let cmdPickerListening = false;
let cmdState = null;
let imageEditorIndex = -1;
let imageEditorData = null;
let imageShot = null;
let imageShotMode = 'sample';
let imageDragStart = null;
let imageSelection = null;
const ROW_HEIGHT = 36;
const INDENT_WIDTH = 25;
const BLOCK_INSET = 8;
const OVERSCAN_ROWS = 12;

// ── Helpers ───────────────────────────────────────────────────────────────────
function fmt(s) {
  s = Math.max(0, Math.floor(s));
  return String(Math.floor(s / 60)).padStart(2,'0') + ':' + String(s % 60).padStart(2,'0');
}

function isKeyType(t) {
  return t === 'KEY_DOWN' || t === 'KEY_UP' || t === 'KEY_PRESS';
}

function normalizeKey(v) {
  const raw = String(v || '').trim();
  if (!raw) return '0x41';
  if (raw.toLowerCase().startsWith('0x')) return '0x' + raw.slice(2).toUpperCase();
  const found = keyOptions.find(([n]) => n.toLowerCase() === raw.toLowerCase());
  return found ? found[1] : raw;
}

function eventBinding(e) {
  if (e.code === 'Space' || e.key === ' ') return 'SPACE';
  return String(e.key || '').toUpperCase();
}

function normalizeBlock(block) {
  const type = (block.type || '').trim();
  if (!supportedBlocks.includes(type)) return null;
  let value = valueLessBlocks.has(type) ? '' : (isKeyType(type) ? normalizeKey(block.value) : String(block.value || '').trim());
  if (type === 'SMOOTH_MOVE') {
    const parts = value.split(',').map(p => p.trim());
    value = parts.length >= 2 ? `${parts[0]},${parts[1]}` : value;
  }
  return { type, value, locked: !!block.locked };
}

function normalizeBlocksList(list) {
  return (list || []).map(normalizeBlock).filter(Boolean);
}

const ME_BASE = window.MACRO_ENGINE_BASE || '/me';

async function api(url, opts = {}) {
  const r = await fetch(ME_BASE + url, opts);
  return r.json();
}

function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function sensitivity() {
  const recH = Number(currentMeta.SENS_RECORDED_H ?? 17);
  const recV = Number(currentMeta.SENS_RECORDED_V ?? 17);
  return {
    SENS_RECORDED_H: recH,
    SENS_RECORDED_V: recV,
    SENS_USER_H: Number(appUserSensitivity.SENS_USER_H ?? recH),
    SENS_USER_V: Number(appUserSensitivity.SENS_USER_V ?? recV),
  };
}

function macroSensitivityForSave() {
  const ui = sensitivity();
  return {
    SENS_RECORDED_H: Number(currentMeta.SENS_RECORDED_H ?? ui.SENS_RECORDED_H),
    SENS_RECORDED_V: Number(currentMeta.SENS_RECORDED_V ?? ui.SENS_RECORDED_V),
    SENS_USER_H: Number(appUserSensitivity.SENS_USER_H ?? ui.SENS_USER_H),
    SENS_USER_V: Number(appUserSensitivity.SENS_USER_V ?? ui.SENS_USER_V),
  };
}

function clampTimes(value) {
  const n = parseInt(String(value ?? playbackTimesValue ?? 5), 10);
  return Number.isFinite(n) && n >= 1 ? n : 5;
}

function setPlayModeFromRepeat(repeat, times) {
  const n = Math.max(0, parseInt(String(repeat ?? 1), 10) || 0);
  playbackTimesValue = clampTimes(times != null ? times : (n > 1 ? n : playbackTimesValue));
  if (n === 0) playbackMode = 'loop';
  else if (n === 1) playbackMode = 'once';
  else {
    playbackMode = 'times';
    playbackTimesValue = n;
  }
}

function applyPlayModeUI() {
  if (playModeSelect) playModeSelect.value = playbackMode;
  if (playModeTimes) {
    playModeTimes.hidden = playbackMode !== 'times';
    playModeTimes.value = String(playbackTimesValue);
  }
}

function playbackRepeat() {
  if (playModeSelect) playbackMode = playModeSelect.value || playbackMode;
  if (playbackMode === 'loop') {
    playbackRepeatValue = 0;
  } else if (playbackMode === 'times') {
    playbackTimesValue = clampTimes(playModeTimes ? playModeTimes.value : playbackTimesValue);
    playbackRepeatValue = playbackTimesValue;
  } else {
    playbackMode = 'once';
    playbackRepeatValue = 1;
  }
  applyPlayModeUI();
  return playbackRepeatValue;
}

function fillBindingSelect(select, value) {
  select.innerHTML = '';
  bindingOptions.forEach(([label, val]) => {
    const o = document.createElement('option');
    o.value = val;
    o.textContent = label;
    if (val === value) o.selected = true;
    select.appendChild(o);
  });
}

function syncSensitivityPair(input, slider) {
  const clamp = value => Math.max(1, Math.min(100, Number(value || 17)));
  input.min = '1';
  input.max = '100';
  const syncFromInput = () => {
    const v = clamp(input.value);
    input.value = String(v);
    slider.value = String(v);
  };
  const syncFromSlider = () => { input.value = Number(slider.value || 17).toFixed(1); };
  input.addEventListener('input', syncFromInput);
  slider.addEventListener('input', syncFromSlider);
  syncFromInput();
}

function syncSensitivitySliders() {
  [
    [sensRh, sensRhSlider],
    [sensRv, sensRvSlider],
    [sensUh, sensUhSlider],
    [sensUv, sensUvSlider],
  ].forEach(([input, slider]) => {
    if (input && slider) slider.value = input.value || 17;
  });
}

async function saveSettingsOnly(opts = {}) {
  recordBindingValue = (recordBinding && recordBinding.value) || recordBindingValue || 'F5';
  playBindingValue = (playBinding && playBinding.value) || playBindingValue || 'F6';
  smoothMoveBindingValue = (smoothMoveBinding && smoothMoveBinding.value) || smoothMoveBindingValue || 'L';
  playbackRepeatValue = playbackRepeat();
  appUserSensitivity = {
    SENS_USER_H: Number((sensUh && sensUh.value) || appUserSensitivity.SENS_USER_H || 17),
    SENS_USER_V: Number((sensUv && sensUv.value) || appUserSensitivity.SENS_USER_V || 17),
  };
  const res = await api('/api/settings', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      sensitivity: sensitivity(),
      record_binding: recordBindingValue,
      play_binding: playBindingValue,
      smooth_binding: smoothMoveBindingValue,
      playback_repeat: playbackRepeatValue,
      playback_times: playbackTimesValue,
    }),
  });
  if (!res.ok) {
    if (!opts.silent) alert(res.error || 'Settings save failed.');
    return false;
  }
  recordBindingValue = res.record_binding || recordBindingValue;
  playBindingValue = res.play_binding || playBindingValue;
  smoothMoveBindingValue = res.smooth_binding || smoothMoveBindingValue;
  playbackRepeatValue = Number(res.playback_repeat ?? playbackRepeatValue);
  playbackTimesValue = clampTimes(res.playback_times ?? playbackTimesValue);
  setPlayModeFromRepeat(playbackRepeatValue, playbackTimesValue);
  applyPlayModeUI();
  fillBindingSelect(recordBinding, recordBindingValue);
  fillBindingSelect(playBinding, playBindingValue);
  if (smoothMoveBinding) fillBindingSelect(smoothMoveBinding, smoothMoveBindingValue);
  updateRunUI({ running, recording });
  return true;
}

function showModal(el) {
  modalBackdrop.classList.remove('hidden');
  el.classList.remove('hidden');
}
function hideModals() {
  const cancelPicker = (pointPickerListening && pointPickerModal && !pointPickerModal.classList.contains('hidden'))
    || (cmdPickerListening && cmdModal && !cmdModal.classList.contains('hidden'));
  modalBackdrop.classList.add('hidden');
  pointPickerSession += 1;
  pointPickerListening = false;
  cmdPickerSession += 1;
  cmdPickerListening = false;
  [saveAsModal, blockPickerModal, fileBrowserModal, pointPickerModal, imageEditorModal, smoothMoveModal, cmdModal].filter(Boolean).forEach(m => m.classList.add('hidden'));
  if (cancelPicker) {
    fetch(ME_BASE + '/api/tools/picker/cancel', { method: 'POST', keepalive: true }).catch(() => {});
  }
}

function closeMenus() {
  menuWraps.forEach(w => w.classList.remove('open'));
}

function scheduleAutosave() {
  if (!currentPath) return;
  clearTimeout(autosaveTimer);
  autosaveTimer = setTimeout(async () => {
    if (!currentPath || isSaving) return;
    await saveCurrent(undefined, undefined, { silent: true, reload: false, sensitivityOverride: macroSensitivityForSave() });
  }, 450);
}

function markEdited() {
  updateRunUI({ running, recording });
  scheduleAutosave();
}

// ── Render ────────────────────────────────────────────────────────────────────
function addBlock(type, value = undefined) {
  if (!supportedBlocks.includes(type)) return;
  let val = value ?? blockDefaults[type] ?? '';
  if ((type === 'IF' || type === 'ELSE_IF') && value === undefined) {
    val = JSON.stringify({ mode: 'boolean', name: nearestBooleanVariableName(), value: true });
  }
  if (isKeyType(type)) val = normalizeKey(val);
  blocks.push({ type, value: val });
  renderBlocks();
  blocksDiv.scrollTop = blocksDiv.scrollHeight;
  scheduleRenderBlocks();
  markEdited();
}

function closeBlockPicker() {
  hideModals();
}

function openBlockPicker(category) {
  if (category === 'mouse') { openCmdDialog('mouse'); return; }
  if (category === 'keyboard') { openCmdDialog('keyboard'); return; }
  const group = pickerGroups[category];
  if (!group) return;
  blockPickerTitle.textContent = group.title;
  blockPickerOptions.innerHTML = '';
  group.options.forEach(([type, title, desc]) => {
    const b = document.createElement('button');
    b.className = 'picker-option';
    b.innerHTML = `<span class="picker-option-title">${title}</span><span class="picker-option-desc">${desc}</span>`;
    b.onclick = () => {
      closeBlockPicker();
      addBlock(type);
    };
    blockPickerOptions.appendChild(b);
  });
  showModal(blockPickerModal);
}

function addSimpleCategory(category) {
  if (category === 'delay') { openCmdDialog('delay'); return; }
  if (category === 'repeat') { openCmdDialog('repeat'); return; }
  if (category === 'end_repeat') { addBlock('ENDREPEAT', ''); return; }
  if (category === 'label') { openCmdDialog('label'); return; }
  if (category === 'goto') { openCmdDialog('goto'); return; }
  if (category === 'variable') { openCmdDialog('variable'); return; }
  if (category === 'set_variable') { openCmdDialog('set_variable'); return; }
  if (category === 'image') {
    addBlock('IMAGE');
    openImageEditor(blocks.length - 1);
    return;
  }
  if (category === 'if') { openCmdDialog('if', null, 'IF'); return; }
  if (category === 'else_if') { openCmdDialog('if', null, 'ELSE_IF'); return; }
  if (category === 'end_if') { addBlock('END_IF'); return; }
  if (category === 'play_macro') { openCmdDialog('play_macro'); return; }
}

const MOUSE_EVENTS = [
  ['SMOOTH_MOVE', 'Smooth Move (In Game)'],
  ['MOUSE_MOVE_ABS', 'Absolute Move (In Menus)'],
  ['MOUSE_LEFT_CLICK', 'Click'],
  ['MOUSE_LEFT_DOWN', 'Left Down'],
  ['MOUSE_LEFT_UP', 'Left Up'],
];
const KEY_EVENTS = [
  ['KEY_PRESS', 'Key Press'],
  ['KEY_DOWN', 'Key Down'],
  ['KEY_UP', 'Key Up'],
];

function isMouseType(t) {
  return ['MOUSE_MOVE_ABS', 'MOUSE_REL', 'SMOOTH_MOVE', 'MOUSE_LEFT_CLICK', 'MOUSE_LEFT_DOWN', 'MOUSE_LEFT_UP'].includes(t);
}
function mouseNeedsXY(t) {
  return t === 'MOUSE_MOVE_ABS' || t === 'SMOOTH_MOVE' || t === 'MOUSE_REL';
}

function fillCmdSelect(sel, items, current) {
  sel.innerHTML = '';
  items.forEach(([value, label]) => {
    const o = document.createElement('option');
    o.value = value;
    o.textContent = label;
    if (value === current) o.selected = true;
    sel.appendChild(o);
  });
}

function fillCmdKeys(currentHex) {
  cmdKey.innerHTML = '';
  const want = String(currentHex || '').toUpperCase();
  keyOptions.forEach(([name, hex]) => {
    const o = document.createElement('option');
    o.value = hex;
    o.textContent = name;
    if (hex.toUpperCase() === want) o.selected = true;
    cmdKey.appendChild(o);
  });
}

function setCmdSection(el, on) {
  if (el) el.classList.toggle('hidden', !on);
}

function updateCmdFields() {
  const kind = cmdState?.kind;
  const type = cmdEventType ? cmdEventType.value : '';
  const mouse = kind === 'mouse';
  setCmdSection(cmdEventWrap, kind === 'mouse' || kind === 'keyboard' || kind === 'if');
  setCmdSection(cmdMouseFields, mouse && mouseNeedsXY(type));
  setCmdSection(cmdKeyFields, kind === 'keyboard');
  setCmdSection(cmdSimpleFields, ['delay', 'repeat', 'label', 'goto'].includes(kind));
  setCmdSection(cmdPlayFields, kind === 'play_macro');
  setCmdSection(cmdVarFields, kind === 'variable');
  setCmdSection(cmdSetFields, kind === 'set_variable');
  setCmdSection(cmdIfFields, kind === 'if');
  if (cmdF2Hint) cmdF2Hint.classList.toggle('hidden', type !== 'MOUSE_MOVE_ABS');
  if (kind === 'variable' && cmdVarType) {
    const isBool = cmdVarType.value === 'boolean';
    setCmdSection(cmdVarValueWrap, !isBool);
    setCmdSection(cmdVarBoolWrap, isBool);
  }
  if (kind === 'set_variable' && cmdSetOp) {
    setCmdSection(cmdSetValueWrap, cmdSetOp.value !== 'toggle');
  }
  if (kind === 'if' && cmdIfMode) {
    const num = cmdIfMode.value === 'number';
    setCmdSection(cmdIfBoolWrap, !num);
    setCmdSection(cmdIfNumWrap, num);
  }
  if (type === 'MOUSE_MOVE_ABS') {
    cmdHint.textContent = 'Moves the cursor to screen coordinates (menus / UI). Press F2 to capture the current position.';
    startCmdPicker();
  } else if (type === 'SMOOTH_MOVE') {
    cmdHint.textContent = 'In-game camera turn (Smooth Move). X/Y are relative mouse counts, not screen pixels.';
    stopCmdPicker();
  } else if (mouse) {
    cmdHint.textContent = 'Sends this mouse event to the active window.';
    stopCmdPicker();
  } else if (kind === 'keyboard') {
    cmdHint.textContent = 'Sends this keystroke to the currently active window.';
    stopCmdPicker();
  } else if (kind === 'delay') {
    cmdHint.textContent = 'Wait before the next command, in milliseconds.';
    stopCmdPicker();
  } else if (kind === 'repeat') {
    cmdHint.textContent = 'Repeat the following blocks until End Repeat.';
    stopCmdPicker();
  } else if (kind === 'label') {
    cmdHint.textContent = 'Named marker that Goto can jump to.';
    stopCmdPicker();
  } else if (kind === 'goto') {
    cmdHint.textContent = 'Jump to a label in this macro.';
    stopCmdPicker();
  } else if (kind === 'play_macro') {
    cmdHint.textContent = 'Play another .macro file, then continue.';
    stopCmdPicker();
  } else if (kind === 'variable') {
    cmdHint.textContent = 'Create a number or boolean variable.';
    stopCmdPicker();
  } else if (kind === 'set_variable') {
    cmdHint.textContent = 'Change an existing variable.';
    stopCmdPicker();
  } else if (kind === 'if') {
    cmdHint.textContent = 'Run following blocks when the condition is true.';
    stopCmdPicker();
  } else {
    cmdHint.textContent = '';
    stopCmdPicker();
  }
}

function stopCmdPicker() {
  cmdPickerSession += 1;
  cmdPickerListening = false;
  fetch(ME_BASE + '/api/tools/picker/cancel', { method: 'POST', keepalive: true }).catch(() => {});
}

function startCmdPicker() {
  if (!cmdModal || cmdModal.classList.contains('hidden')) return;
  if (cmdEventType.value !== 'MOUSE_MOVE_ABS') return;
  cmdPickerSession += 1;
  const session = cmdPickerSession;
  runCmdPicker(session);
}

async function runCmdPicker(session) {
  if (cmdPickerListening || session !== cmdPickerSession) return;
  if (!cmdModal || cmdModal.classList.contains('hidden')) return;
  cmdPickerListening = true;
  try {
    const d = await api('/api/tools/picker', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ timeout: 3600 }),
    });
    if (session !== cmdPickerSession || cmdModal.classList.contains('hidden')) return;
    if (d && d.ok) {
      cmdX.value = String(d.x);
      cmdY.value = String(d.y);
      cmdF2Hint.textContent = `Captured ${d.x}, ${d.y} — press F2 again to recapture`;
    }
  } catch {
  } finally {
    cmdPickerListening = false;
    if (session === cmdPickerSession && cmdModal && !cmdModal.classList.contains('hidden') && cmdEventType.value === 'MOUSE_MOVE_ABS') {
      setTimeout(() => runCmdPicker(session), 80);
    }
  }
}

function openCmdDialog(kind, index = null, forceType = null) {
  const block = index != null ? blocks[index] : null;
  cmdState = { kind, index };
  const titles = {
    mouse: 'mouse command',
    keyboard: 'keyboard command',
    delay: 'delay',
    repeat: 'repeat',
    label: 'label',
    goto: 'goto',
    play_macro: 'play macro',
    variable: 'variable',
    set_variable: 'set variable',
    if: 'condition',
  };
  cmdTitle.textContent = index == null ? `Add ${titles[kind] || 'command'}` : `Edit ${titles[kind] || 'command'}`;
  const type = forceType || block?.type || '';
  if (kind === 'keyboard') {
    fillCmdSelect(cmdEventType, KEY_EVENTS, isKeyType(type) ? type : 'KEY_PRESS');
    fillCmdKeys(block?.value || blockDefaults.KEY_PRESS);
  } else if (kind === 'mouse') {
    const mouseType = isMouseType(type) && type !== 'MOUSE_REL' ? type : 'SMOOTH_MOVE';
    fillCmdSelect(cmdEventType, MOUSE_EVENTS, mouseType);
    const parts = String(block?.value || (mouseType === 'SMOOTH_MOVE' ? '60,0' : '960,540')).split(',');
    cmdX.value = (parts[0] ?? '0').trim() || '0';
    cmdY.value = (parts[1] ?? '0').trim() || '0';
    cmdF2Hint.textContent = 'Press F2 to capture current screen position';
  } else if (kind === 'delay') {
    if (cmdSimpleName) cmdSimpleName.textContent = 'Milliseconds';
    cmdSimple.value = block?.value || blockDefaults.DELAY;
  } else if (kind === 'repeat') {
    if (cmdSimpleName) cmdSimpleName.textContent = 'Repeat count';
    cmdSimple.value = block?.value || blockDefaults.REPEAT;
  } else if (kind === 'label') {
    if (cmdSimpleName) cmdSimpleName.textContent = 'Label name';
    cmdSimple.value = block?.value || blockDefaults.LABEL;
  } else if (kind === 'goto') {
    if (cmdSimpleName) cmdSimpleName.textContent = 'Goto label';
    cmdSimple.value = block?.value || blockDefaults.GOTO;
  } else if (kind === 'play_macro') {
    const current = String(block?.value || '').trim();
    cmdPlayPath.value = current ? filenameFromPath(current) : '';
    cmdPlayPath.dataset.path = current;
    cmdPlayPath.title = current;
  } else if (kind === 'variable') {
    const data = block ? parseBlockJson(block) : { name: 'var1', var_type: 'number', value: 0 };
    cmdVarName.value = data.name || 'var1';
    cmdVarType.value = data.var_type === 'boolean' ? 'boolean' : 'number';
    cmdVarValue.value = String(data.value ?? 0);
    cmdVarBool.value = data.value === true ? 'true' : 'false';
  } else if (kind === 'set_variable') {
    const data = block ? parseBlockJson(block) : { name: 'var1', op: 'set', value: 0 };
    cmdSetName.value = data.name || 'var1';
    cmdSetOp.value = data.op || 'set';
    cmdSetValue.value = String(data.value ?? 0);
  } else if (kind === 'if') {
    fillCmdSelect(cmdEventType, [['IF', 'If'], ['ELSE_IF', 'Else If']], type === 'ELSE_IF' ? 'ELSE_IF' : 'IF');
    const data = block ? parseBlockJson(block) : { mode: 'boolean', name: nearestBooleanVariableName(), value: true, op: '>=' };
    cmdIfName.value = data.name || 'image_found';
    cmdIfMode.value = data.mode === 'number' ? 'number' : 'boolean';
    cmdIfBool.value = data.value === false ? 'false' : 'true';
    cmdIfOp.value = data.op || '>=';
    cmdIfValue.value = String(data.value ?? 0);
  }
  showModal(cmdModal);
  updateCmdFields();
}

function applyCmdDialog() {
  if (!cmdState) return;
  const kind = cmdState.kind;
  let type = cmdEventType.value;
  let value = '';
  if (kind === 'keyboard') {
    value = cmdKey.value;
  } else if (kind === 'mouse') {
    if (mouseNeedsXY(type)) {
      value = `${String(cmdX.value || '0').trim() || '0'},${String(cmdY.value || '0').trim() || '0'}`;
    }
  } else if (kind === 'delay') {
    type = 'DELAY';
    value = String(cmdSimple.value || '100').trim() || '100';
  } else if (kind === 'repeat') {
    type = 'REPEAT';
    value = String(cmdSimple.value || '2').trim() || '2';
  } else if (kind === 'label') {
    type = 'LABEL';
    value = String(cmdSimple.value || 'START').trim() || 'START';
  } else if (kind === 'goto') {
    type = 'GOTO';
    value = String(cmdSimple.value || 'START').trim() || 'START';
  } else if (kind === 'play_macro') {
    type = 'PLAY_MACRO';
    value = cmdPlayPath.dataset.path || '';
    if (!value) { alert('Select a macro.'); return; }
  } else if (kind === 'variable') {
    type = 'VARIABLE';
    const isBool = cmdVarType.value === 'boolean';
    value = JSON.stringify({
      name: cmdVarName.value.trim() || 'var1',
      var_type: isBool ? 'boolean' : 'number',
      value: isBool ? cmdVarBool.value === 'true' : Number(cmdVarValue.value || 0),
    });
  } else if (kind === 'set_variable') {
    type = 'SET_VARIABLE';
    value = JSON.stringify({
      name: cmdSetName.value.trim() || 'var1',
      op: cmdSetOp.value || 'set',
      value: cmdSetOp.value === 'toggle' ? 0 : Number(cmdSetValue.value || 0),
    });
  } else if (kind === 'if') {
    type = cmdEventType.value === 'ELSE_IF' ? 'ELSE_IF' : 'IF';
    const num = cmdIfMode.value === 'number';
    value = JSON.stringify(num ? {
      mode: 'number',
      name: cmdIfName.value.trim() || 'var1',
      op: cmdIfOp.value || '>=',
      value: Number(cmdIfValue.value || 0),
    } : {
      mode: 'boolean',
      name: cmdIfName.value.trim() || 'image_found',
      value: cmdIfBool.value === 'true',
    });
  }
  const idx = cmdState.index;
  const addRepeatEnd = kind === 'repeat' && idx == null;
  hideModals();
  if (idx == null) {
    addBlock(type, value);
    if (addRepeatEnd) addBlock('ENDREPEAT', '');
  } else if (blocks[idx]) {
    blocks[idx].type = type;
    blocks[idx].value = isKeyType(type) ? normalizeKey(value) : value;
    renderBlocks();
    markEdited();
  }
  cmdState = null;
}

function openEditForBlock(index) {
  const t = blocks[index]?.type;
  if (!t) return;
  if (isMouseType(t)) openCmdDialog('mouse', index);
  else if (isKeyType(t)) openCmdDialog('keyboard', index);
  else if (t === 'DELAY') openCmdDialog('delay', index);
  else if (t === 'REPEAT') openCmdDialog('repeat', index);
  else if (t === 'LABEL') openCmdDialog('label', index);
  else if (t === 'GOTO') openCmdDialog('goto', index);
  else if (t === 'PLAY_MACRO') openCmdDialog('play_macro', index);
  else if (t === 'VARIABLE') openCmdDialog('variable', index);
  else if (t === 'SET_VARIABLE') openCmdDialog('set_variable', index);
  else if (t === 'IF' || t === 'ELSE_IF') openCmdDialog('if', index);
  else if (t === 'IMAGE') openImageEditor(index);
}

function parseBlockJson(block) {
  const fallback = blockDefaults[block.type] || '{}';
  try { return JSON.parse(block.value || fallback); }
  catch { return JSON.parse(fallback); }
}

function writeBlockJson(index, data) {
  blocks[index].value = JSON.stringify(data);
  markEdited();
}

function variableNames() {
  const names = [];
  blocks.forEach(b => {
    try {
      const data = JSON.parse(b.value || '{}');
      const name = b.type === 'IMAGE' ? data.var : data.name;
      if (name && !names.includes(name)) names.push(name);
    } catch {}
  });
  return names;
}

function nearestBooleanVariableName() {
  for (let i = blocks.length - 1; i >= 0; i--) {
    const b = blocks[i];
    try {
      const data = JSON.parse(b.value || '{}');
      if (b.type === 'IMAGE' && data.var) return data.var;
      if (b.type === 'VARIABLE' && data.var_type === 'boolean' && data.name) return data.name;
    } catch {}
  }
  return 'image_found';
}

function makeVarInput(data, key, index, placeholder = 'var1') {
  const wrap = document.createElement('span');
  wrap.className = 'mini-field';
  const input = document.createElement('input');
  input.type = 'text';
  input.placeholder = placeholder;
  input.value = data[key] || '';
  const listId = `var-list-${index}-${key}`;
  const list = document.createElement('datalist');
  list.id = listId;
  variableNames().forEach(name => {
    const opt = document.createElement('option');
    opt.value = name;
    list.appendChild(opt);
  });
  input.setAttribute('list', listId);
  input.className = 'bauble';
  input.addEventListener('input', () => { data[key] = input.value.trim(); writeBlockJson(index, data); });
  wrap.appendChild(input);
  wrap.appendChild(list);
  return wrap;
}

function addOption(select, value, label, selected) {
  const o = document.createElement('option');
  o.value = value;
  o.textContent = label;
  if (selected) o.selected = true;
  select.appendChild(o);
}

function numericInput(data, key, index, attrs = {}) {
  const input = document.createElement('input');
  input.type = 'text';
  input.inputMode = 'numeric';
  input.className = 'bauble';
  input.value = data[key] ?? 0;
  Object.entries(attrs).forEach(([k, v]) => input.setAttribute(k, v));
  input.addEventListener('input', () => { data[key] = Number(input.value || 0); writeBlockJson(index, data); });
  return input;
}

function textInput(data, key, index, placeholder = '') {
  const input = document.createElement('input');
  input.type = 'text';
  input.value = data[key] || '';
  input.placeholder = placeholder;
  input.addEventListener('input', () => { data[key] = input.value; writeBlockJson(index, data); });
  return input;
}

async function requestRegion() {
  const res = await api('/api/tools/region', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ timeout: 120 }),
  });
  if (!res.ok) throw new Error(res.error || 'Region pick failed.');
  return res;
}

async function captureImageRegion(region, name) {
  const res = await api('/api/tools/image/capture', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ...region, name, base_w: imageShot?.width, base_h: imageShot?.height }),
  });
  if (!res.ok) throw new Error(res.error || 'Image capture failed.');
  return res;
}

async function saveImageSample(image, region, name, baseW, baseH) {
  const res = await api('/api/tools/image/save-sample', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ...region, image, name, base_w: baseW, base_h: baseH }),
  });
  if (!res.ok) throw new Error(res.error || 'Image sample save failed.');
  return res;
}

async function testImageCurrent(data) {
  const res = await api('/api/tools/image/test', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(res.error || 'Image test failed.');
  return res;
}

async function refreshImagePathList() {
  if (!imagePathList && !imagePathSelect) return;
  const current = imagePathInput?.value?.trim() || '';
  try {
    const res = await api('/api/tools/image/list');
    if (!res.ok) return;
    if (imagePathList) imagePathList.innerHTML = '';
    if (imagePathSelect) {
      imagePathSelect.innerHTML = '';
      const blank = document.createElement('option');
      blank.value = '';
      blank.textContent = 'Select image...';
      imagePathSelect.appendChild(blank);
    }
    (res.images || []).forEach(item => {
      const value = item.path || item.name || '';
      const opt = document.createElement('option');
      opt.value = value;
      if (imagePathList) imagePathList.appendChild(opt);
      if (imagePathSelect) {
        const selectOpt = document.createElement('option');
        selectOpt.value = value;
        selectOpt.textContent = item.name || value;
        imagePathSelect.appendChild(selectOpt);
      }
    });
    if (imagePathSelect) imagePathSelect.value = current;
  } catch (_) {}
}

async function requestFullscreenShot() {
  const res = await api('/api/tools/screenshot');
  if (!res.ok) throw new Error(res.error || 'Screenshot failed.');
  return res;
}

function imageNumberInputValue(el, fallback = 0) {
  return Number(el.value || fallback);
}

function readImageEditorForm() {
  if (!imageEditorData) return null;
  return {
    ...imageEditorData,
    var: imageVarInput.value.trim() || 'image_found',
    result_mode: imageResultMode.value || 'bool',
    x_var: imageXVarInput.value.trim(),
    y_var: imageYVarInput.value.trim(),
    path: imagePathInput.value.trim(),
    threshold: Math.max(1, Math.min(100, Number(imageThresholdInput.value || 85))),
    fixed: !!imageFixedInput.checked,
    x1: imageNumberInputValue(imageX1),
    y1: imageNumberInputValue(imageY1),
    x2: imageNumberInputValue(imageX2),
    y2: imageNumberInputValue(imageY2),
    search_x1: imageNumberInputValue(imageSearchX1),
    search_y1: imageNumberInputValue(imageSearchY1),
    search_x2: imageNumberInputValue(imageSearchX2),
    search_y2: imageNumberInputValue(imageSearchY2),
  };
}

function writeImageEditorForm(data) {
  const boolName = data.var || 'image_found';
  imageVarInput.value = boolName;
  imageResultMode.value = data.result_mode || 'bool';
  imageXVarInput.value = data.x_var || `${boolName}_x`;
  imageYVarInput.value = data.y_var || `${boolName}_y`;
  imagePathInput.value = data.path || '';
  if (imagePathSelect) imagePathSelect.value = data.path || '';
  imageThresholdInput.value = data.threshold ?? 85;
  imageFixedInput.checked = data.fixed !== false;
  imageX1.value = data.x1 ?? 0;
  imageY1.value = data.y1 ?? 0;
  imageX2.value = data.x2 ?? 100;
  imageY2.value = data.y2 ?? 100;
  imageSearchX1.value = data.search_x1 ?? 0;
  imageSearchY1.value = data.search_y1 ?? 0;
  imageSearchX2.value = data.search_x2 ?? 1920;
  imageSearchY2.value = data.search_y2 ?? 1080;
  [imageSearchX1, imageSearchY1, imageSearchX2, imageSearchY2, imageSelectSearch].forEach(el => { el.disabled = data.fixed !== false; });
}

function saveImageEditorData({ close = false } = {}) {
  if (imageEditorIndex < 0) return;
  imageEditorData = readImageEditorForm();
  writeBlockJson(imageEditorIndex, imageEditorData);
  renderBlocks();
  if (close) hideModals();
}

function drawImageShot() {
  if (!imageShot || !imageShot.img) return;
  const ctx = imageShotCanvas.getContext('2d');
  imageShotCanvas.width = imageShot.width;
  imageShotCanvas.height = imageShot.height;
  ctx.drawImage(imageShot.img, 0, 0);
  if (imageSelection) {
    const x = Math.min(imageSelection.x1, imageSelection.x2) - imageShot.left;
    const y = Math.min(imageSelection.y1, imageSelection.y2) - imageShot.top;
    const w = Math.abs(imageSelection.x2 - imageSelection.x1);
    const h = Math.abs(imageSelection.y2 - imageSelection.y1);
    ctx.save();
    ctx.fillStyle = 'rgba(124,106,247,.18)';
    ctx.strokeStyle = '#f7a06a';
    ctx.lineWidth = Math.max(2, Math.round(imageShot.width / 900));
    ctx.fillRect(x, y, w, h);
    ctx.strokeRect(x, y, w, h);
    ctx.restore();
  }
}

function canvasPointToScreen(e) {
  const rect = imageShotCanvas.getBoundingClientRect();
  const x = (e.clientX - rect.left) * (imageShotCanvas.width / rect.width);
  const y = (e.clientY - rect.top) * (imageShotCanvas.height / rect.height);
  return {
    x: Math.round(imageShot.left + Math.max(0, Math.min(imageShot.width, x))),
    y: Math.round(imageShot.top + Math.max(0, Math.min(imageShot.height, y))),
  };
}

async function startImageScreenshotPick(mode) {
  imageShotMode = mode;
  imageSelection = null;
  imageApplySelection.disabled = true;
  imageShotStatus.textContent = mode === 'sample' ? 'Loading fullscreen screenshot for sample selection...' : 'Loading fullscreen screenshot for search area...';
  imageShotWrap.classList.remove('hidden');
  const shot = await requestFullscreenShot();
  const img = new Image();
  await new Promise((resolve, reject) => {
    img.onload = resolve;
    img.onerror = reject;
    img.src = `data:image/png;base64,${shot.image}`;
  });
  imageShot = { ...shot, img };
  imageShotStatus.textContent = mode === 'sample'
    ? 'Drag a box around the exact image sample.'
    : 'Drag a box where the macro should search for the sample.';
  drawImageShot();
}

function openImageEditor(index) {
  imageEditorIndex = index;
  imageEditorData = parseBlockJson(blocks[index]);
  imageShot = null;
  imageSelection = null;
  imageApplySelection.disabled = true;
  imageShotWrap.classList.add('hidden');
  imageShotStatus.textContent = '';
  writeImageEditorForm(imageEditorData);
  refreshImagePathList();
  showModal(imageEditorModal);
}

function imageBlockSummary(data) {
  const name = data.var || 'image_found';
  const threshold = data.threshold ?? 85;
  const mode = data.fixed === false ? 'search area' : 'same XY';
  const out = data.result_mode === 'coords'
    ? `${data.x_var || `${name}_x`},${data.y_var || `${name}_y`}`
    : (data.result_mode === 'both' ? `${name}+XY` : name);
  const path = data.path ? data.path.split(/[\\/]/).pop() : 'no sample';
  return `${out} = ${path} @ ${threshold}% (${mode})`;
}

function createLogicEditor(block, index) {
  const data = parseBlockJson(block);
  const wrap = document.createElement('div');
  wrap.className = `complex-editor ${block.type.toLowerCase()}-editor`;

  if (block.type === 'VARIABLE') {
    wrap.appendChild(makeVarInput(data, 'name', index, 'variable'));
    const typeSel = document.createElement('select');
    typeSel.className = 'bauble';
    addOption(typeSel, 'number', 'Number', data.var_type !== 'boolean');
    addOption(typeSel, 'boolean', 'Boolean', data.var_type === 'boolean');
    typeSel.addEventListener('change', () => {
      data.var_type = typeSel.value;
      data.value = typeSel.value === 'boolean' ? Boolean(data.value) : Number(data.value || 0);
      writeBlockJson(index, data);
      renderBlocks();
    });
    wrap.appendChild(typeSel);
    if (data.var_type === 'boolean') {
      const boolSel = document.createElement('select');
      boolSel.className = 'bauble';
      addOption(boolSel, 'true', 'True', data.value === true);
      addOption(boolSel, 'false', 'False', data.value !== true);
      boolSel.addEventListener('change', () => { data.value = boolSel.value === 'true'; writeBlockJson(index, data); });
      wrap.appendChild(boolSel);
    } else {
      wrap.appendChild(numericInput(data, 'value', index, { step: '1' }));
    }
    return wrap;
  }

  if (block.type === 'SET_VARIABLE') {
    wrap.appendChild(makeVarInput(data, 'name', index, 'variable'));
    const opSel = document.createElement('select');
    opSel.className = 'bauble';
    [['set','Set'],['add','+ Add'],['subtract','- Subtract'],['toggle','Toggle']].forEach(([v, label]) => addOption(opSel, v, label, data.op === v));
    opSel.addEventListener('change', () => { data.op = opSel.value; writeBlockJson(index, data); renderBlocks(); });
    wrap.appendChild(opSel);
    if (data.op !== 'toggle') wrap.appendChild(numericInput(data, 'value', index, { step: '1' }));
    return wrap;
  }

  if (block.type === 'IMAGE') {
    wrap.classList.add('image-summary-editor');
    const summary = document.createElement('span');
    summary.className = 'image-summary';
    summary.textContent = imageBlockSummary(data);
    wrap.appendChild(summary);
    const edit = document.createElement('button');
    edit.type = 'button';
    edit.className = 'mini-action neutral';
    edit.textContent = 'Edit';
    edit.onclick = () => openImageEditor(index);
    wrap.appendChild(edit);
    return wrap;
  }

  if (block.type === 'IF' || block.type === 'ELSE_IF') {
    const mode = document.createElement('select');
    mode.className = 'bauble';
    addOption(mode, 'boolean', 'Boolean', data.mode !== 'number');
    addOption(mode, 'number', 'Number', data.mode === 'number');
    mode.addEventListener('change', () => { data.mode = mode.value; writeBlockJson(index, data); renderBlocks(); });
    wrap.appendChild(mode);
    wrap.appendChild(makeVarInput(data, 'name', index, 'variable'));
    if (data.mode === 'number') {
      const op = document.createElement('select');
      op.className = 'bauble';
      ['>=','>','==','!=','<','<='].forEach(v => addOption(op, v, v, (data.op || '>=') === v));
      op.addEventListener('change', () => { data.op = op.value; writeBlockJson(index, data); });
      wrap.appendChild(op);
      wrap.appendChild(numericInput(data, 'value', index, { step: '1' }));
    } else {
      const boolSel = document.createElement('select');
      boolSel.className = 'bauble';
      addOption(boolSel, 'true', 'is True', data.value !== false);
      addOption(boolSel, 'false', 'is False', data.value === false);
      boolSel.addEventListener('change', () => { data.value = boolSel.value === 'true'; writeBlockJson(index, data); });
      wrap.appendChild(boolSel);
    }
    return wrap;
  }

  const empty = document.createElement('div');
  empty.className = 'value-empty';
  return empty;
}

const CATEGORY_MAP = {
  LABEL:            { icon: 'label.png',       label: 'Label' },
  GOTO:             { icon: 'goto.png',        label: 'Goto' },
  DELAY:            { icon: 'delay.png',       label: 'Delay' },
  KEY_DOWN:         { icon: 'keyboard.png',     label: 'Keyboard' },
  KEY_UP:           { icon: 'keyboard.png',     label: 'Keyboard' },
  KEY_PRESS:        { icon: 'keyboard.png',     label: 'Keyboard' },
  MOUSE_MOVE_ABS:   { icon: 'mouse.png',        label: 'Mouse' },
  MOUSE_LEFT_DOWN:  { icon: 'mouse.png',        label: 'Mouse' },
  MOUSE_LEFT_UP:    { icon: 'mouse.png',        label: 'Mouse' },
  MOUSE_LEFT_CLICK: { icon: 'mouse.png',        label: 'Mouse' },
  MOUSE_REL:        { icon: 'mouse.png',        label: 'Mouse' },
  SMOOTH_MOVE:      { icon: 'mouse.png',        label: 'Mouse' },
  REPEAT:           { icon: 'repeat.png',       label: 'Repeat' },
  ENDREPEAT:        { icon: 'end_repeat.png',   label: 'End Repeat' },
  VARIABLE:         { icon: 'variable.png',     label: 'Variable' },
  SET_VARIABLE:     { icon: 'set_variable.png', label: 'Set Variable' },
  IMAGE:            { icon: 'image.png',        label: 'Image' },
  IF:               { icon: 'if.png',           label: 'If' },
  ELSE_IF:          { icon: 'else_if.png',      label: 'Else If' },
  END_IF:           { icon: 'end_if.png',       label: 'End If' },
  PLAY_MACRO:       { icon: 'play_macro.png',   label: 'Macro' },
};

const ACTION_LABELS = {
  LABEL: 'Label', GOTO: 'Goto Label', DELAY: 'Delay',
  KEY_DOWN: 'Key Down', KEY_UP: 'Key Up', KEY_PRESS: 'Key Press',
  MOUSE_MOVE_ABS: 'Absolute Move', MOUSE_LEFT_DOWN: 'Left Down', MOUSE_LEFT_UP: 'Left Up',
  MOUSE_LEFT_CLICK: 'Click', MOUSE_REL: 'Move Relative', SMOOTH_MOVE: 'Smooth Move',
  REPEAT: 'Repeat', ENDREPEAT: 'End Repeat',
  VARIABLE: 'Define Variable', SET_VARIABLE: 'Set Variable', IMAGE: 'Check Image',
  IF: 'If', ELSE_IF: 'Else If', END_IF: 'End If',
  PLAY_MACRO: 'Play Macro',
};

const ACTIONS_COL_WIDTH = 58;
const DEFAULT_COL_WIDTHS = [120, 148, 180, 180, ACTIONS_COL_WIDTH];
const MIN_COL_WIDTH = 48;
const MIN_VAR_COL_WIDTH = 64;

function loadColWidths() {
  try {
    const saved = JSON.parse(localStorage.getItem('me_col_widths') || 'null');
    if (Array.isArray(saved) && saved.length >= 4 && saved.every(n => Number.isFinite(n) && n > 0)) {
      const next = DEFAULT_COL_WIDTHS.slice();
      next[0] = saved[0];
      next[1] = saved[1];
      next[2] = saved[2];
      next[3] = saved[3];
      next[4] = ACTIONS_COL_WIDTH;
      return next;
    }
  } catch {}
  return DEFAULT_COL_WIDTHS.slice();
}

let colWidths = loadColWidths();
let selectedIndices = new Set();
let selectionAnchor = null;
let dragIndices = [];
let blockClipboard = [];
const CLIP_PREFIX = 'MT2BLOCKS:';
const blockCtxMenu = document.getElementById('blockCtxMenu');
let colsFittedSig = '';
let _measureCtx = null;

function measureTextPx(text) {
  if (!_measureCtx) _measureCtx = document.createElement('canvas').getContext('2d');
  _measureCtx.font = '600 12px "Segoe UI", system-ui, sans-serif';
  return Math.ceil(_measureCtx.measureText(String(text || '')).width);
}

function panelWidth() {
  return Math.max(360, blocksDiv.clientWidth || 0);
}

function contentLabelWidths() {
  let cat = measureTextPx('Keyboard');
  let type = measureTextPx('Absolute Move');
  let maxIndent = 0;
  for (let i = 0; i < blocks.length; i++) {
    const t = blocks[i]?.type;
    if (!t) continue;
    const info = CATEGORY_MAP[t] || { label: t };
    cat = Math.max(cat, measureTextPx(info.label || t));
    type = Math.max(type, measureTextPx(ACTION_LABELS[t] || t));
    maxIndent = Math.max(maxIndent, blockIndentFor(i));
  }
  cat = Math.min(240, Math.max(92, cat + 15 + 7 + 16 + maxIndent * 14));
  type = Math.min(220, Math.max(108, type + 28));
  return [cat, type];
}

function normalizeColWidths(splitVars = false) {
  colWidths[4] = ACTIONS_COL_WIDTH;
  const flexBudget = Math.max(MIN_COL_WIDTH * 4, panelWidth() - ACTIONS_COL_WIDTH);
  for (let i = 0; i < 4; i++) {
    colWidths[i] = Math.max(i < 2 ? MIN_COL_WIDTH : MIN_VAR_COL_WIDTH, Number(colWidths[i]) || MIN_COL_WIDTH);
  }
  if (splitVars) {
    const rest = flexBudget - colWidths[0] - colWidths[1];
    colWidths[2] = Math.max(MIN_VAR_COL_WIDTH, Math.floor(rest / 2));
    colWidths[3] = Math.max(MIN_VAR_COL_WIDTH, rest - colWidths[2]);
    return;
  }
  let sum = colWidths[0] + colWidths[1] + colWidths[2] + colWidths[3];
  if (sum > flexBudget) {
    let overflow = sum - flexBudget;
    for (const i of [3, 2, 1, 0]) {
      const floor = i < 2 ? MIN_COL_WIDTH : MIN_VAR_COL_WIDTH;
      const take = Math.min(Math.max(0, colWidths[i] - floor), overflow);
      colWidths[i] -= take;
      overflow -= take;
      if (overflow <= 0) break;
    }
  } else {
    colWidths[3] += flexBudget - sum;
  }
}

function fitColumnsToContent(force = false) {
  const sig = `${blocks.map(b => b.type).join(',')}|${panelWidth()}`;
  if (!force && sig === colsFittedSig) {
    normalizeColWidths(false);
    return;
  }
  colsFittedSig = sig;
  const [cat, type] = contentLabelWidths();
  colWidths[0] = cat;
  colWidths[1] = type;
  normalizeColWidths(true);
}

function persistColWidths() {
  try { localStorage.setItem('me_col_widths', JSON.stringify(colWidths)); } catch {}
}

function emptyVarCell() {
  const d = document.createElement('div');
  d.className = 'var-empty';
  return d;
}

function createGenericInput(block, index) {
  const inp = document.createElement('input');
  inp.type = 'text';
  inp.className = 'var-input';
  inp.value = block.value || '';
  inp.placeholder = blockDefaults[block.type] ?? '';
  inp.addEventListener('input', () => { blocks[index].value = inp.value; markEdited(); });
  return inp;
}

function createKeySelect(block, index) {
  const sel = document.createElement('select');
  sel.className = 'var-input';
  keyOptions.forEach(([name, hex]) => {
    const o = document.createElement('option');
    o.value       = hex;
    o.textContent = name;
    if (hex.toUpperCase() === String(block.value || '').toUpperCase()) o.selected = true;
    sel.appendChild(o);
  });
  sel.addEventListener('change', () => { blocks[index].value = sel.value; markEdited(); });
  return sel;
}

function createXYEditor(block, index) {
  const parts = String(block.value || '').split(',');
  const va = parts[0] !== undefined ? parts[0].trim() : '0';
  const vb = parts[1] !== undefined ? parts[1].trim() : '0';
  const a = document.createElement('input');
  a.type = 'text'; a.inputMode = 'numeric'; a.className = 'var-input'; a.value = va; a.spellcheck = false;
  const b = document.createElement('input');
  b.type = 'text'; b.inputMode = 'numeric'; b.className = 'var-input'; b.value = vb; b.spellcheck = false;
  const sync = () => { blocks[index].value = `${a.value || 0},${b.value || 0}`; markEdited(); };
  a.addEventListener('input', sync);
  b.addEventListener('input', sync);
  return [a, b];
}

function createPlayMacroEditor(block, index) {
  const wrap = document.createElement('div');
  wrap.className = 'complex-editor play-macro-editor';
  const pathInput = document.createElement('input');
  pathInput.type = 'text';
  pathInput.className = 'path-input';
  pathInput.readOnly = true;
  const current = String(block.value || '').trim();
  pathInput.value = current ? filenameFromPath(current) : '';
  pathInput.placeholder = 'Select macro';
  pathInput.title = current || 'Select macro';
  wrap.appendChild(pathInput);
  const browseBtn = document.createElement('button');
  browseBtn.type = 'button';
  browseBtn.className = 'mini-action';
  browseBtn.textContent = 'Browse…';
  browseBtn.addEventListener('click', async () => {
    const d = await pickMacroFileDialog();
    if (!d) return;
    blocks[index].value = d;
    markEdited();
    renderBlocks();
  });
  wrap.appendChild(browseBtn);
  return wrap;
}

function buildVarCells(block, index) {
  const type = block.type;
  if (valueLessBlocks.has(type)) {
    return { mode: 'split', a: emptyVarCell(), b: emptyVarCell() };
  }
  if (['VARIABLE', 'SET_VARIABLE', 'IMAGE', 'IF', 'ELSE_IF'].includes(type)) {
    return { mode: 'span', el: createLogicEditor(block, index) };
  }
  if (type === 'PLAY_MACRO') {
    return { mode: 'span', el: createPlayMacroEditor(block, index) };
  }
  if (['MOUSE_MOVE_ABS', 'MOUSE_REL', 'SMOOTH_MOVE'].includes(type)) {
    const [a, b] = createXYEditor(block, index);
    return { mode: 'split', a, b };
  }
  if (isKeyType(type)) {
    return { mode: 'split', a: createKeySelect(block, index), b: emptyVarCell() };
  }
  return { mode: 'split', a: createGenericInput(block, index), b: emptyVarCell() };
}

function buildCategoryCell(type, indentDepth) {
  const cell = document.createElement('div');
  cell.className = 'cat-cell';
  cell.style.paddingLeft = `${8 + indentDepth * 14}px`;
  const info = CATEGORY_MAP[type] || { icon: '', label: type };
  if (info.icon) {
    const img = document.createElement('img');
    img.className = 'cat-icon';
    img.src = `/me/static/icons/${info.icon}`;
    img.alt = '';
    cell.appendChild(img);
  }
  const span = document.createElement('span');
  span.className = 'cat-label';
  span.textContent = info.label;
  cell.appendChild(span);
  return cell;
}

function blockIndentFor(index) {
  let depth = 0;
  for (let i = 0; i < index; i++) {
    const t = blocks[i]?.type;
    if (t === 'IF' || t === 'REPEAT') depth += 1;
    if (t === 'END_IF' || t === 'ENDREPEAT') depth = Math.max(0, depth - 1);
  }
  const current = blocks[index]?.type;
  if (current === 'ELSE_IF' || current === 'END_IF' || current === 'ENDREPEAT') depth = Math.max(0, depth - 1);
  return depth;
}

function gridTemplateColumnsCss() {
  return colWidths.map(w => `${w}px`).join(' ');
}

function applyColumnWidths() {
  normalizeColWidths();
  const template = gridTemplateColumnsCss();
  blocksDiv.querySelectorAll('.block').forEach(row => { row.style.gridTemplateColumns = template; });
  let x = 0;
  blocksDiv.querySelectorAll('.col-divider').forEach((div) => {
    const i = Number(div.dataset.colIndex);
    x = colWidths.slice(0, i + 1).reduce((a, b) => a + b, 0);
    div.style.left = `${x}px`;
  });
  const end = blocksDiv.querySelector('.col-end');
  if (end) {
    end.style.left = `${colWidths[0] + colWidths[1] + colWidths[2] + colWidths[3]}px`;
  }
}

function appendColumnDividers(totalHeight) {
  const lineHeight = Math.max(totalHeight, blocksDiv.clientHeight || 0);
  let x = 0;
  for (let i = 0; i < 3; i++) {
    x += colWidths[i];
    const div = document.createElement('div');
    div.className = 'col-divider';
    div.dataset.colIndex = String(i);
    div.style.left = `${x}px`;
    div.style.height = `${lineHeight}px`;
    div.addEventListener('mousedown', startColumnResize);
    blocksDiv.appendChild(div);
  }
  const end = document.createElement('div');
  end.className = 'col-end';
  end.style.left = `${colWidths[0] + colWidths[1] + colWidths[2] + colWidths[3]}px`;
  end.style.height = `${lineHeight}px`;
  blocksDiv.appendChild(end);
}

function startColumnResize(e) {
  e.preventDefault();
  e.stopPropagation();
  const idx = Number(e.currentTarget.dataset.colIndex);
  if (idx < 0 || idx > 2) return;
  const startX = e.clientX;
  const startWidths = colWidths.slice();
  e.currentTarget.classList.add('resizing');
  const onMove = (ev) => {
    const dx = ev.clientX - startX;
    if (idx === 2) {
      const pair = startWidths[2] + startWidths[3];
      colWidths[2] = Math.min(pair - MIN_VAR_COL_WIDTH, Math.max(MIN_VAR_COL_WIDTH, startWidths[2] + dx));
      colWidths[3] = pair - colWidths[2];
    } else {
      colWidths[idx] = Math.max(MIN_COL_WIDTH, startWidths[idx] + dx);
      normalizeColWidths(false);
    }
    applyColumnWidths();
  };
  const onUp = () => {
    document.removeEventListener('mousemove', onMove);
    document.removeEventListener('mouseup', onUp);
    e.currentTarget.classList.remove('resizing');
    persistColWidths();
  };
  document.addEventListener('mousemove', onMove);
  document.addEventListener('mouseup', onUp);
}

function clearSelection() {
  if (!selectedIndices.size) return;
  selectedIndices = new Set();
  selectionAnchor = null;
}

function cloneBlock(b) {
  return { type: b.type, value: b.value || '', locked: !!b.locked };
}

function selectedSorted() {
  return Array.from(selectedIndices).sort((a, b) => a - b);
}

function isTypingTarget(el) {
  if (!el) return false;
  const tag = (el.tagName || '').toLowerCase();
  if (tag === 'input' || tag === 'textarea' || tag === 'select') return true;
  return !!el.isContentEditable;
}

function copySelectedBlocks() {
  const idxs = selectedSorted();
  if (!idxs.length) return false;
  blockClipboard = idxs.map(i => cloneBlock(blocks[i]));
  try {
    navigator.clipboard.writeText(CLIP_PREFIX + JSON.stringify(blockClipboard));
  } catch {}
  return true;
}

function cutSelectedBlocks() {
  if (!selectedIndices.size) return;
  copySelectedBlocks();
  removeSelectedBlocks();
}

function removeSelectedBlocks() {
  if (!selectedIndices.size) return;
  const toRemove = new Set(selectedIndices);
  blocks = blocks.filter((_, i) => !toRemove.has(i));
  clearSelection();
  renderBlocks();
  markEdited();
}

async function pasteBlocks() {
  let payload = blockClipboard;
  try {
    const text = await navigator.clipboard.readText();
    if (text && text.startsWith(CLIP_PREFIX)) {
      const parsed = JSON.parse(text.slice(CLIP_PREFIX.length));
      if (Array.isArray(parsed) && parsed.length) payload = parsed;
    }
  } catch {}
  if (!payload.length) return;
  const copies = payload.map(cloneBlock).map(b => normalizeBlock(b)).filter(Boolean);
  if (!copies.length) return;
  const insertAt = selectedIndices.size ? Math.max(...selectedIndices) + 1 : blocks.length;
  blocks.splice(insertAt, 0, ...copies);
  selectedIndices = new Set(copies.map((_, k) => insertAt + k));
  selectionAnchor = insertAt;
  renderBlocks();
  markEdited();
}

function hideCtxMenu() {
  if (blockCtxMenu) blockCtxMenu.classList.add('hidden');
}

function showCtxMenu(x, y) {
  if (!blockCtxMenu) return;
  const hasSel = selectedIndices.size > 0;
  const hasClip = blockClipboard.length > 0;
  blockCtxMenu.querySelectorAll('button').forEach(btn => {
    const act = btn.dataset.act;
    btn.disabled = (
      (act === 'edit' && selectedIndices.size !== 1) ||
      (act === 'cut' && !hasSel) ||
      (act === 'copy' && !hasSel) ||
      (act === 'remove' && !hasSel) ||
      (act === 'paste' && !hasClip)
    );
  });
  blockCtxMenu.classList.remove('hidden');
  const w = blockCtxMenu.offsetWidth || 188;
  const h = blockCtxMenu.offsetHeight || 180;
  const left = Math.min(x, window.innerWidth - w - 8);
  const top = Math.min(y, window.innerHeight - h - 8);
  blockCtxMenu.style.left = `${Math.max(8, left)}px`;
  blockCtxMenu.style.top = `${Math.max(8, top)}px`;
}

function handleRowContextMenu(e, i) {
  e.preventDefault();
  e.stopPropagation();
  if (!selectedIndices.has(i)) {
    selectedIndices = new Set([i]);
    selectionAnchor = i;
    renderBlocks();
  }
  showCtxMenu(e.clientX, e.clientY);
}

function handleRowClick(e, i) {
  if (e.target.closest('input,select,button,textarea')) return;
  if (e.shiftKey && selectionAnchor !== null) {
    const lo = Math.min(selectionAnchor, i);
    const hi = Math.max(selectionAnchor, i);
    selectedIndices = new Set();
    for (let k = lo; k <= hi; k++) selectedIndices.add(k);
  } else if (e.ctrlKey || e.metaKey) {
    selectedIndices = new Set(selectedIndices);
    if (selectedIndices.has(i)) selectedIndices.delete(i); else selectedIndices.add(i);
    selectionAnchor = i;
  } else {
    selectedIndices = new Set([i]);
    selectionAnchor = i;
  }
  renderBlocks();
}

function handleDragStart(e, i, row) {
  if (!selectedIndices.has(i)) {
    selectedIndices = new Set([i]);
    selectionAnchor = i;
  }
  dragIndices = Array.from(selectedIndices).sort((a, b) => a - b);
  row.classList.add('dragging');
  e.dataTransfer.effectAllowed = 'move';
  e.dataTransfer.setData('text/plain', String(i));
}

function handleDrop(e, targetIndex) {
  e.preventDefault();
  if (!dragIndices.length) return;
  if (dragIndices.includes(targetIndex)) { dragIndices = []; return; }
  const movingSet = new Set(dragIndices);
  const moving = dragIndices.map(idx => blocks[idx]);
  const remaining = blocks.filter((_, idx) => !movingSet.has(idx));
  const removedBefore = dragIndices.filter(idx => idx < targetIndex).length;
  const insertAt = Math.max(0, Math.min(targetIndex - removedBefore, remaining.length));
  remaining.splice(insertAt, 0, ...moving);
  blocks = remaining;
  selectedIndices = new Set();
  for (let k = 0; k < moving.length; k++) selectedIndices.add(insertAt + k);
  selectionAnchor = insertAt;
  dragIndices = [];
  renderBlocks();
  markEdited();
}

function renderBlocks() {
  const scrollTop = blocksDiv.scrollTop || 0;
  const viewport = blocksDiv.clientHeight || 600;
  fitColumnsToContent();
  const start = Math.max(0, Math.floor(scrollTop / ROW_HEIGHT) - OVERSCAN_ROWS);
  const end = Math.min(blocks.length, Math.ceil((scrollTop + viewport) / ROW_HEIGHT) + OVERSCAN_ROWS);
  blocksDiv.innerHTML = '';
  const totalHeight = blocks.length * ROW_HEIGHT;
  const canvasH = Math.max(totalHeight, blocksDiv.clientHeight || 0);
  const spacer = document.createElement('div');
  spacer.className = 'blocks-spacer';
  spacer.style.height = `${canvasH}px`;
  blocksDiv.appendChild(spacer);
  appendColumnDividers(canvasH);

  const gridTemplate = gridTemplateColumnsCss();

  for (let i = start; i < end; i++) {
    const b = blocks[i];
    const row = document.createElement('div');
    row.className       = 'block';
    row.draggable       = true;
    row.dataset.index   = i;
    row.style.transform = `translateY(${i * ROW_HEIGHT}px)`;
    row.style.gridTemplateColumns = gridTemplate;
    if (b.locked) row.classList.add('block-locked');
    if (selectedIndices.has(i)) row.classList.add('selected');

    row.appendChild(buildCategoryCell(b.type, blockIndentFor(i)));

    const typeBtn = document.createElement('button');
    typeBtn.type = 'button';
    typeBtn.className = 'type-btn';
    typeBtn.textContent = ACTION_LABELS[b.type] || b.type;
    typeBtn.title = 'Edit command';
    typeBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      openEditForBlock(i);
    });
    row.appendChild(typeBtn);

    const cells = buildVarCells(b, i);
    if (cells.mode === 'span') {
      cells.el.style.gridColumn = '3 / span 2';
      row.appendChild(cells.el);
    } else {
      row.appendChild(cells.a);
      row.appendChild(cells.b);
    }

    const actions = document.createElement('div');
    actions.className = 'actions-cell';

    const lock = document.createElement('button');
    lock.type = 'button';
    lock.className = `lock-btn ${b.locked ? 'is-locked' : 'is-unlocked'}`;
    lock.title = b.locked ? 'Locked — survives macro recording (click to unlock)' : 'Unlocked (click to lock)';
    lock.addEventListener('click', (e) => {
      e.stopPropagation();
      blocks[i].locked = !blocks[i].locked;
      markEdited();
      renderBlocks();
    });
    actions.appendChild(lock);

    const del = document.createElement('button');
    del.type = 'button';
    del.className = 'del-btn';
    del.textContent = '✕';
    del.title       = 'Remove';
    del.addEventListener('click', (e) => {
      e.stopPropagation();
      if (selectedIndices.has(i) && selectedIndices.size > 1) {
        const toRemove = new Set(selectedIndices);
        blocks = blocks.filter((_, idx) => !toRemove.has(idx));
        clearSelection();
      } else {
        blocks.splice(i, 1);
      }
      renderBlocks();
      markEdited();
    });
    actions.appendChild(del);

    row.appendChild(actions);

    row.addEventListener('click', e => handleRowClick(e, i));
    row.addEventListener('contextmenu', e => handleRowContextMenu(e, i));
    row.addEventListener('dblclick', (e) => {
      if (e.target.closest('button,input,select,textarea')) return;
      openEditForBlock(i);
    });
    row.addEventListener('dragstart', e => handleDragStart(e, i, row));
    row.addEventListener('dragend', () => row.classList.remove('dragging'));
    row.addEventListener('dragover', e => e.preventDefault());
    row.addEventListener('drop', e => handleDrop(e, Number(row.dataset.index)));

    blocksDiv.appendChild(row);
  }
  blocksDiv.scrollTop = scrollTop;
  updateRunUI({ running, recording });
}

function scheduleRenderBlocks() {
  if (renderScheduled) return;
  renderScheduled = true;
  requestAnimationFrame(() => {
    renderScheduled = false;
    renderBlocks();
  });
}

function renderRecorderHint() {
  const hint = document.querySelector('.top-hint');
  if (!hint) return;
  const rec = recordBindingValue || 'F5';
  const play = playBindingValue || 'F6';
  hint.textContent = `${rec} record · ${play} play`;
  if (recordBtnTop) recordBtnTop.title = `Record (${rec})`;
  if (playStopBtn) playStopBtn.title = `Play / Stop (${play})`;
}

function renderMeta() {
  const file = currentPath
    ? String(currentPath).replace(/\\/g, '/').split('/').pop()
    : (currentMacro ? `${String(currentMacro).replace(/\.macro$/i, '')}.macro` : 'No macro');
  if (macroTopLabel) {
    macroTopLabel.textContent = file;
    macroTopLabel.title = currentPath || file;
  }
}

function macroRelKey(m) {
  return String((m && (m.rel || m.name)) || '').replace(/\\/g, '/').replace(/\.macro$/i, '');
}
function macroHintFor(m) {
  if (!m) return '';
  const rel = macroRelKey(m);
  const base = rel.split('/').pop();
  return MACRO_HINTS[rel] || MACRO_HINTS[base] || '';
}
function folderLabel(folder) {
  const key = String(folder || '');
  if (MACRO_FOLDER_LABELS[key]) return MACRO_FOLDER_LABELS[key];
  return key.replace(/_/g, ' ');
}
function updateMacroHint() {
  if (!macroHintBtn || !macroHintPop) return;
  const path = macroQuickSelect ? macroQuickSelect.value : currentPath;
  const m = macroList.find(x => x.path === path) || null;
  const hint = macroHintFor(m);
  macroHintBtn.hidden = !hint;
  macroHintPop.textContent = hint;
  if (!hint) macroHintPop.classList.add('hidden');
}

function renderMacroList() {
  if (!macroQuickSelect) return;
  const keep = currentPath;
  const groups = new Map();
  for (const m of macroList) {
    const folder = m.folder || '';
    if (!groups.has(folder)) groups.set(folder, []);
    groups.get(folder).push(m);
  }
  const folders = [...groups.keys()].sort((a, b) => {
    const ia = MACRO_FOLDER_ORDER.indexOf(a);
    const ib = MACRO_FOLDER_ORDER.indexOf(b);
    if (ia >= 0 || ib >= 0) return (ia < 0 ? 999 : ia) - (ib < 0 ? 999 : ib);
    return String(a).localeCompare(String(b));
  });
  macroQuickSelect.innerHTML = '';
  const ph = document.createElement('option');
  ph.value = '';
  ph.disabled = true;
  ph.textContent = '- MACROS -';
  macroQuickSelect.appendChild(ph);
  if (!macroList.length) {
    const o = document.createElement('option');
    o.textContent = '(no macros in folder)';
    macroQuickSelect.appendChild(o);
    updateMacroHint();
    return;
  }
  for (const folder of folders) {
    const og = document.createElement('optgroup');
    og.label = folderLabel(folder);
    for (const m of groups.get(folder)) {
      const o = document.createElement('option');
      o.value = m.path;
      o.textContent = m.name + (macroHintFor(m) ? '' : '');
      og.appendChild(o);
    }
    macroQuickSelect.appendChild(og);
  }
  if (keep) macroQuickSelect.value = keep;
  updateMacroHint();
}

if (macroQuickSelect) {
  macroQuickSelect.addEventListener('change', async () => {
    const p = macroQuickSelect.value;
    if (!p) return;
    if (p === currentPath) { updateMacroHint(); return; }
    await loadMacroByPath(p);
    updateMacroHint();
  });
}
if (macroHintBtn && macroHintPop) {
  const showHint = () => {
    if (macroHintBtn.hidden) return;
    if (macroHintPop.textContent) macroHintPop.classList.remove('hidden');
  };
  const hideHint = () => macroHintPop.classList.add('hidden');
  macroHintBtn.addEventListener('mouseenter', showHint);
  macroHintBtn.addEventListener('focus', showHint);
  const wrap = macroHintBtn.closest('.macro-select-wrap');
  if (wrap) wrap.addEventListener('mouseleave', hideHint);
  macroHintBtn.addEventListener('blur', hideHint);
}

// ── State polling (overlay data) ──────────────────────────────────────────────
function updateRunUI(st) {
  running = !!st.running;
  recording = !!st.recording;
  const elapsed   = parseFloat(st.elapsed   || 0);
  const estimated = parseFloat(st.estimated || 0);
  const progress  = Math.min(1, Math.max(0, parseFloat(st.progress || 0)));

  const pct = (progress * 100).toFixed(1);
  progressBar.style.width = pct + '%';
  progressBar.className   = 'progress-fill' + ((running || recording) ? '' : ' done');

  macroLabel.textContent = st.macro || currentMacro || '-';
  timeLabel.textContent  = fmt(elapsed) + ' / ' + fmt(estimated);

  recordBtnTop.textContent = recording ? '■' : '●';
  recordBtnTop.title = recording ? 'Stop Recording' : 'Record';
  recordBtnTop.disabled = running;
  playStopBtn.textContent = running ? '■' : '▶';
  playStopBtn.title = running ? 'Stop' : 'Play';
  playStopBtn.disabled = recording || (!running && blocks.length === 0);
}

async function pollState() {
  try {
    const d = await api('/api/state');
    const st = d.state || {};
    const recordVersion = Number(st.record_version || 0);
    const recordPath = st.record_path || '';
    const sm = d.smooth_move || {};
    const smSeq = Number(sm.seq || 0);
    if (smSeq > lastSmoothMoveSeq) {
      lastSmoothMoveSeq = smSeq;
      const smX = Math.round(Number(sm.x || 0));
      const smY = Math.round(Number(sm.y || 0));
      if ((Math.abs(smX) >= 1 || Math.abs(smY) >= 1) && smoothMoveResult && smoothMoveModal) {
        smoothMoveResult.value = `(${smX}, ${smY})`;
        smoothMoveStatus.textContent = 'Copied as "' + smX + ',' + smY + '" — paste into a Smooth Move block.';
        showModal(smoothMoveModal);
      }
    }
    updateRunUI(st);
    if (!recording && recordVersion > lastRecordVersion && recordPath) {
      lastRecordVersion = recordVersion;
      await loadMacroByPath(recordPath);
      await refreshMacroList();
      return;
    }
    if (recordVersion > lastRecordVersion) lastRecordVersion = recordVersion;
  } catch (_) {}
}

// ── Load a macro from server (by path) ───────────────────────────────────────
async function loadMacroByPath(path) {
  const d = await api(`/api/macro/open?path=${encodeURIComponent(path)}`);
  if (!d.ok) { alert(d.error || 'Failed to load.'); return; }
  applyLoadedMacro(d);
}

// ── Save current macro ────────────────────────────────────────────────────────
async function saveCurrent(path, name, options = {}) {
  const silent = !!options.silent;
  const reload = options.reload !== false;
  clearTimeout(autosaveTimer);
  const sensitivityPayload = options.sensitivityOverride || macroSensitivityForSave();
  const p = path || currentPath;
  const n = name || currentMacro || 'macro';
  if (!p) {
    if (!silent) openSaveAs();
    return false;
  }
  if (isSaving) return false;
  isSaving = true;
  const res = await api('/api/macro/save', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path: p, name: n, blocks: normalizeBlocksList(blocks), sensitivity: sensitivityPayload }),
  });
  isSaving = false;
  if (!res.ok) {
    if (!silent) alert(res.error || 'Save failed');
    return false;
  }
  if (reload) {
    applyLoadedMacro(res);
  } else {
    currentPath = res.path || p;
    currentMacro = res.name || n;
    currentMeta = { ...(res.meta || currentMeta) };
    renderMeta();
  }
  return true;
}

function filenameFromPath(path) {
  return String(path || '').replace(/.*[\\/]/, '');
}

function joinBrowserPath(dir, file) {
  dir = String(dir || '').trim();
  file = String(file || '').trim();
  if (!dir) return file;
  if (/[\\/]$/.test(dir)) return dir + file;
  return dir + '\\' + file;
}

async function loadBrowserDir(path) {
  fileBrowserStatus.textContent = 'Loading...';
  const d = await api(`/api/fs/list?path=${encodeURIComponent(path || browserDir || currentPath || '')}`);
  if (!d.ok) {
    fileBrowserStatus.textContent = d.error || 'Could not open folder.';
    fileBrowserEntries.innerHTML = '';
    return;
  }
  browserDir = d.path || '';
  browserParent = d.parent || '';
  browserFile = '';
  fileBrowserPath.value = browserDir;
  fileBrowserStatus.textContent = '';

  fileBrowserRoots.innerHTML = '';
  (d.roots || []).forEach(root => {
    const b = document.createElement('button');
    b.textContent = root;
    b.onclick = () => loadBrowserDir(root);
    fileBrowserRoots.appendChild(b);
  });

  fileBrowserEntries.innerHTML = '';
  (d.entries || []).forEach(entry => {
    const row = document.createElement('div');
    row.className = 'file-entry';
    row.dataset.path = entry.path;
    const kind = document.createElement('span');
    kind.className = 'file-kind';
    kind.textContent = entry.is_dir ? 'DIR' : 'MAC';
    const name = document.createElement('span');
    name.textContent = entry.name;
    const meta = document.createElement('span');
    meta.className = 'file-path';
    meta.textContent = entry.is_dir ? 'folder' : '.macro';
    row.appendChild(kind);
    row.appendChild(name);
    row.appendChild(meta);
    row.onclick = () => {
      document.querySelectorAll('.file-entry.selected').forEach(e => e.classList.remove('selected'));
      row.classList.add('selected');
      if (entry.is_dir) {
        browserFile = '';
      } else {
        browserFile = entry.path;
        fileBrowserName.value = entry.name;
      }
    };
    row.ondblclick = () => {
      if (entry.is_dir) {
        loadBrowserDir(entry.path);
      } else if (browserMode === 'open') {
        chooseBrowserFile(entry.path);
      }
    };
    fileBrowserEntries.appendChild(row);
  });
}

async function openFileBrowser(mode) {
  browserMode = mode;
  browserFile = '';
  fileBrowserHead.textContent = mode === 'save' ? 'Save Macro As' : 'Open Macro';
  fileBrowserConfirm.textContent = mode === 'save' ? 'Save' : 'Open';
  fileBrowserNameWrap.style.display = mode === 'save' ? 'block' : 'none';
  fileBrowserName.value = mode === 'save'
    ? ((currentMacro || 'macro').replace(/\.macro$/i, '') + '.macro')
    : '';
  showModal(fileBrowserModal);
  await loadBrowserDir(currentPath || '');
}

async function chooseBrowserFile(path) {
  if (!path) return;
  hideModals();
  await loadMacroByPath(path);
  await refreshMacroList();
  renderMeta();
}

async function confirmFileBrowser() {
  if (browserMode === 'open') {
    if (!browserFile) {
      fileBrowserStatus.textContent = 'Select a .macro file first.';
      return;
    }
    await chooseBrowserFile(browserFile);
    return;
  }

  let name = fileBrowserName.value.trim();
  if (!name) {
    fileBrowserStatus.textContent = 'Enter a file name.';
    return;
  }
  if (!name.toLowerCase().endsWith('.macro')) name += '.macro';
  const path = joinBrowserPath(browserDir, name);
  hideModals();
  const ok = await saveCurrent(path, name.replace(/\.macro$/i, ''));
  if (ok) await refreshMacroList();
}

async function openPointPicker() {
  closeMenus();
  pointPickerResult.value = '';
  pointPickerStatus.textContent = 'Hover anywhere and press F2 to take sample.';
  showModal(pointPickerModal);
  pointPickerSession += 1;
  startPointPicker(pointPickerSession);
}

async function startPointPicker(session = pointPickerSession) {
  if (pointPickerListening || session !== pointPickerSession || pointPickerModal.classList.contains('hidden')) return;
  pointPickerListening = true;
  if (pointPickerStart) pointPickerStart.disabled = true;
  pointPickerStatus.textContent = 'Hover anywhere and press F2 to take sample.';
  let keepListening = true;
  try {
    const d = await api('/api/tools/picker', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ timeout: 3600 }),
    });
    if (session !== pointPickerSession || pointPickerModal.classList.contains('hidden')) return;
    if (!d.ok) {
      pointPickerStatus.textContent = d.error || 'Picker failed.';
      return;
    }
    pointPickerResult.value = `${d.x},${d.y}`;
    pointPickerStatus.textContent = 'Picked screen X,Y.';
    pointPickerResult.focus();
    pointPickerResult.select();
  } catch (e) {
    pointPickerStatus.textContent = 'Picker request failed.';
    keepListening = false;
  } finally {
    pointPickerListening = false;
    if (pointPickerStart) pointPickerStart.disabled = false;
    if (keepListening && session === pointPickerSession && !pointPickerModal.classList.contains('hidden')) {
      setTimeout(() => startPointPicker(session), 80);
    }
  }
}

async function copyPickedPoint() {
  const value = pointPickerResult.value || '';
  if (!value) return;
  try {
    await navigator.clipboard.writeText(value);
    pointPickerStatus.textContent = 'Copied X,Y.';
  } catch (e) {
    pointPickerResult.focus();
    pointPickerResult.select();
    pointPickerStatus.textContent = 'X,Y selected.';
  }
}

async function openSaveAs() {
  return openFileBrowser('save');
}

function applyLoadedMacro(d) {
  currentPath  = d.path;
  currentMacro = d.name;
  blocks = normalizeBlocksList(d.blocks || []);
  clearTimeout(autosaveTimer);
  const m = d.meta || {};
  currentMeta = { ...m };
  const userH = Number(appUserSensitivity.SENS_USER_H ?? 17);
  const userV = Number(appUserSensitivity.SENS_USER_V ?? 17);
  if (sensRh) sensRh.value = m.SENS_RECORDED_H ?? 17;
  if (sensRv) sensRv.value = m.SENS_RECORDED_V ?? 17;
  if (sensUh) sensUh.value = userH;
  if (sensUv) sensUv.value = userV;
  syncSensitivitySliders();
  renderMeta();
  renderBlocks();
  if (macroQuickSelect && currentPath) macroQuickSelect.value = currentPath;
  updateMacroHint();
}

function openPathModal(mode) {
  return openFileBrowser('open');
}

async function confirmPathModal() {
  return openFileBrowser('open');
}

async function openNativeMacro() {
  return openFileBrowser('open');
}

async function newMacro() {
  const d = await api('/api/macro/new', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: 'untitled' }),
  });
  if (!d.ok) { alert(d.error || 'Failed to create new macro.'); return; }
  applyLoadedMacro(d);
}

// ── File open (read client-side, send text to server save endpoint) ───────────
function openFileDialog(forImport) {
  return openNativeMacro();
}

function parseBlocks(text) {
  const blocks = [];
  for (const raw of text.split('\n')) {
    const line = raw.trim();
    if (!line || line.startsWith('#')) continue;
    const idx = line.indexOf(':');
    if (idx === -1) {
      blocks.push({ type: line, value: '' });
    } else {
      blocks.push({ type: line.slice(0, idx).trim(), value: line.slice(idx + 1).trim() });
    }
  }
  return blocks;
}

function parseSens(text) {
  const s = { SENS_RECORDED_H: 17, SENS_RECORDED_V: 17, SENS_USER_H: 17, SENS_USER_V: 17 };
  for (const raw of text.split('\n')) {
    const m = raw.match(/^#\s*(SENS_\w+):(.+)/);
    if (m) s[m[1].trim()] = parseFloat(m[2]) || 17;
  }
  return s;
}

async function pickMacroFileDialog() {
  const d = await api('/api/dialog/open');
  if (!d || d.cancelled) return null;
  if (!d.ok) { alert(d.error || 'Could not open file dialog.'); return null; }
  return d.path || null;
}

async function refreshMacroList() {
  const d = await api('/api/macro/list');
  macroList = d.macros || [];
  renderMacroList();
}

// ── Bootstrap ─────────────────────────────────────────────────────────────────
async function bootstrap() {
  const b = await api('/api/bootstrap');
  macroList    = b.macros    || [];
  currentPath  = b.current_path  || '';
  currentMacro = b.current_macro || '';
  lastRecordVersion = Number((b.state || {}).record_version || 0);
  recordBindingValue = b.record_binding || 'F5';
  playBindingValue = b.play_binding || 'F6';
  smoothMoveBindingValue = b.smooth_binding || 'L';
  playbackRepeatValue = Number(b.playback_repeat ?? playbackRepeatValue ?? 1);
  playbackTimesValue = clampTimes(b.playback_times ?? (playbackRepeatValue > 1 ? playbackRepeatValue : 5));
  setPlayModeFromRepeat(playbackRepeatValue, playbackTimesValue);
  applyPlayModeUI();
  if (recordBinding) fillBindingSelect(recordBinding, recordBindingValue);
  if (playBinding) fillBindingSelect(playBinding, playBindingValue);
  if (smoothMoveBinding) fillBindingSelect(smoothMoveBinding, smoothMoveBindingValue);
  renderRecorderHint();
  const bs = b.sensitivity || {};
  appUserSensitivity = {
    SENS_USER_H: Number(bs.SENS_USER_H ?? bs.user_h ?? 17),
    SENS_USER_V: Number(bs.SENS_USER_V ?? bs.user_v ?? 17),
  };
  if (sensRh) sensRh.value = bs.SENS_RECORDED_H ?? bs.recorded_h ?? 17;
  if (sensRv) sensRv.value = bs.SENS_RECORDED_V ?? bs.recorded_v ?? 17;
  if (sensUh) sensUh.value = String(appUserSensitivity.SENS_USER_H);
  if (sensUv) sensUv.value = String(appUserSensitivity.SENS_USER_V);
  syncSensitivitySliders();

  renderMacroList();

  if (currentPath) {
    await loadMacroByPath(currentPath);
  } else if (macroList.length) {
    await loadMacroByPath(macroList[0].path);
  }

  updateRunUI(b.state || {});
}

// ── Event wiring ──────────────────────────────────────────────────────────────

if (sensRh && sensRhSlider) syncSensitivityPair(sensRh, sensRhSlider);
if (sensRv && sensRvSlider) syncSensitivityPair(sensRv, sensRvSlider);
if (sensUh && sensUhSlider) syncSensitivityPair(sensUh, sensUhSlider);
if (sensUv && sensUvSlider) syncSensitivityPair(sensUv, sensUvSlider);
blocksDiv.addEventListener('scroll', () => {
  scheduleRenderBlocks();
});
blocksDiv.addEventListener('click', (e) => {
  if (e.target.closest('.block, .col-divider, button, input, select, textarea')) return;
  hideCtxMenu();
  if (!selectedIndices.size) return;
  clearSelection();
  renderBlocks();
});
blocksDiv.addEventListener('contextmenu', (e) => {
  if (e.target.closest('.block')) return;
  e.preventDefault();
  showCtxMenu(e.clientX, e.clientY);
});
if (typeof ResizeObserver !== 'undefined') {
  new ResizeObserver(() => {
    colsFittedSig = '';
    scheduleRenderBlocks();
  }).observe(blocksDiv);
}

document.addEventListener('keydown', (e) => {
  if (isTypingTarget(e.target)) return;
  const mod = e.ctrlKey || e.metaKey;
  const key = String(e.key || '').toLowerCase();
  if (mod && key === 'c') { e.preventDefault(); copySelectedBlocks(); return; }
  if (mod && key === 'x') { e.preventDefault(); cutSelectedBlocks(); return; }
  if (mod && key === 'v') { e.preventDefault(); pasteBlocks(); return; }
  if (e.key === 'Delete') { e.preventDefault(); removeSelectedBlocks(); return; }
  if (e.key === 'Escape') {
    hideCtxMenu();
    if (selectedIndices.size) { clearSelection(); renderBlocks(); }
  }
});

document.addEventListener('click', (e) => {
  if (blockCtxMenu && !blockCtxMenu.contains(e.target)) hideCtxMenu();
});
document.addEventListener('scroll', hideCtxMenu, true);

if (blockCtxMenu) {
  blockCtxMenu.addEventListener('click', (e) => {
    const btn = e.target.closest('button');
    if (!btn || btn.disabled) return;
    const act = btn.dataset.act;
    hideCtxMenu();
    if (act === 'edit') {
      const idx = selectedSorted()[0];
      if (idx != null) openEditForBlock(idx);
    } else if (act === 'cut') cutSelectedBlocks();
    else if (act === 'copy') copySelectedBlocks();
    else if (act === 'paste') pasteBlocks();
    else if (act === 'remove') removeSelectedBlocks();
  });
  blockCtxMenu.addEventListener('contextmenu', e => e.preventDefault());
}

newBtn.onclick    = newMacro;
openBtn.onclick   = openNativeMacro;
importBtn.onclick = openNativeMacro;

saveBtn.onclick       = () => saveCurrent();
saveAsBtn.onclick     = openSaveAs;
if (pickerToolBtn) pickerToolBtn.onclick = openPointPicker;

menuWraps.forEach(wrap => {
  const button = wrap.querySelector('.menu-btn');
  button.addEventListener('click', e => {
    e.stopPropagation();
    const wasOpen = wrap.classList.contains('open');
    closeMenus();
    if (!wasOpen) wrap.classList.add('open');
  });
  wrap.querySelectorAll('.menu-item').forEach(item => {
    item.addEventListener('click', closeMenus);
  });
});
document.addEventListener('click', closeMenus);
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') closeMenus();
});

categoryButtons.forEach(btn => {
  btn.addEventListener('click', () => {
    const category = btn.dataset.category;
    if (pickerGroups[category]) openBlockPicker(category);
    else addSimpleCategory(category);
  });
});

sidebarToggle.onclick = () => {
  sidebar.classList.toggle('collapsed');
  const lbl = sidebarToggle.querySelector('.sb-label');
  if (lbl) lbl.textContent = sidebar.classList.contains('collapsed') ? 'Show panel' : 'Hide panel';
};

blockPickerClose.onclick = closeBlockPicker;
if (cmdEventType) cmdEventType.addEventListener('change', updateCmdFields);
if (cmdVarType) cmdVarType.addEventListener('change', updateCmdFields);
if (cmdSetOp) cmdSetOp.addEventListener('change', updateCmdFields);
if (cmdIfMode) cmdIfMode.addEventListener('change', updateCmdFields);
if (cmdPlayBrowse) {
  cmdPlayBrowse.onclick = async () => {
    const d = await pickMacroFileDialog();
    if (!d) return;
    cmdPlayPath.value = filenameFromPath(d);
    cmdPlayPath.dataset.path = d;
    cmdPlayPath.title = d;
  };
}
if (cmdOk) cmdOk.onclick = applyCmdDialog;
if (cmdCancel) cmdCancel.onclick = hideModals;
if (cmdClose) cmdClose.onclick = hideModals;

saveAsConfirm.onclick = async () => {
  const p = saveAsPath.value.trim();
  const n = saveAsName.value.trim();
  if (!p) { alert('Enter a file path.'); return; }
  hideModals();
  const ok = await saveCurrent(p, n || p.replace(/.*[\\/]/, '').replace(/\.macro$/i, ''));
  if (ok) await refreshMacroList();
};
saveAsCancel.onclick = hideModals;

fileBrowserGo.onclick = () => loadBrowserDir(fileBrowserPath.value.trim());
fileBrowserUp.onclick = () => {
  if (browserParent) loadBrowserDir(browserParent);
};
fileBrowserConfirm.onclick = confirmFileBrowser;
fileBrowserCancel.onclick = hideModals;
fileBrowserPath.addEventListener('keydown', e => {
  if (e.key === 'Enter') loadBrowserDir(fileBrowserPath.value.trim());
});
fileBrowserName.addEventListener('keydown', e => {
  if (e.key === 'Enter') confirmFileBrowser();
});

if (pointPickerStart) pointPickerStart.onclick = () => startPointPicker(pointPickerSession);
pointPickerCopy.onclick = copyPickedPoint;
pointPickerClose.onclick = hideModals;

smoothMoveClose.onclick = hideModals;
smoothMoveCancel.onclick = hideModals;
smoothMoveCopy.onclick = async function () {
  const value = smoothMoveResult.value || '';
  const m = /^\((-?\d+),\s*(-?\d+)\)$/.exec(value);
  const copyText = m ? (m[1] + ',' + m[2]) : value;
  if (!copyText) return;
  try {
    await navigator.clipboard.writeText(copyText);
    smoothMoveStatus.textContent = 'Copied "' + copyText + '".';
  } catch (e) {
    smoothMoveResult.focus();
    smoothMoveResult.select();
    smoothMoveStatus.textContent = 'Field selected — press Ctrl+C.';
  }
};
pointPickerCancel.onclick = hideModals;
pointPickerResult.addEventListener('focus', () => pointPickerResult.select());

function currentImageSelectionRegion() {
  if (!imageSelection) return null;
  const x1 = Math.min(imageSelection.x1, imageSelection.x2);
  const y1 = Math.min(imageSelection.y1, imageSelection.y2);
  const x2 = Math.max(imageSelection.x1, imageSelection.x2);
  const y2 = Math.max(imageSelection.y1, imageSelection.y2);
  if (x2 - x1 < 2 || y2 - y1 < 2) return null;
  return { x1, y1, x2, y2 };
}

function selectedImageCropDataUrl(region) {
  if (!imageShot || !imageShot.img || !region) return "";
  const w = Math.max(1, region.x2 - region.x1);
  const h = Math.max(1, region.y2 - region.y1);
  const canvas = document.createElement('canvas');
  canvas.width = w;
  canvas.height = h;
  const ctx = canvas.getContext('2d');
  ctx.drawImage(
    imageShot.img,
    region.x1 - imageShot.left,
    region.y1 - imageShot.top,
    w,
    h,
    0,
    0,
    w,
    h,
  );
  return canvas.toDataURL('image/png');
}

imageEditorClose.onclick = hideModals;
imageEditorCancel.onclick = hideModals;
imageEditorSave.onclick = () => saveImageEditorData({ close: true });
imageFixedInput.onchange = () => {
  const data = readImageEditorForm();
  imageEditorData = data;
  writeImageEditorForm(data);
};
imageVarInput.addEventListener('input', () => {
  const name = imageVarInput.value.trim() || 'image';
  if (!imageXVarInput.value.trim()) imageXVarInput.value = `${name}_x`;
  if (!imageYVarInput.value.trim()) imageYVarInput.value = `${name}_y`;
});
if (imagePathSelect) imagePathSelect.addEventListener('change', () => {
  if (!imagePathSelect.value) return;
  imagePathInput.value = imagePathSelect.value;
  imageEditorData = readImageEditorForm();
  saveImageEditorData();
  imageShotStatus.textContent = 'Image selected.';
});
imageSelectSample.onclick = async () => {
  try {
    imageEditorData = readImageEditorForm();
    await startImageScreenshotPick('sample');
  } catch (err) {
    imageShotStatus.textContent = err.message || String(err);
  }
};
imageSelectSearch.onclick = async () => {
  try {
    imageEditorData = readImageEditorForm();
    await startImageScreenshotPick('search');
  } catch (err) {
    imageShotStatus.textContent = err.message || String(err);
  }
};
imageTestCurrent.onclick = async () => {
  try {
    imageEditorData = readImageEditorForm();
    imageShotStatus.textContent = 'Testing current screen...';
    const result = await testImageCurrent(imageEditorData);
    const r = result.region || {};
    const where = result.mode ? `${result.mode} ${r.x1 ?? ''},${r.y1 ?? ''}-${r.x2 ?? ''},${r.y2 ?? ''}` : 'current screen';
    imageShotStatus.textContent = result.matched
      ? `MATCH: ${result.score_percent}% >= ${result.threshold}% (${where}) mid ${result.x ?? '?'},${result.y ?? '?'}`
      : `NO MATCH: ${result.score_percent}% < ${result.threshold}% (${where})`;
    saveImageEditorData();
  } catch (err) {
    imageShotStatus.textContent = err.message || String(err);
  }
};
imageApplySelection.onclick = async () => {
  const region = currentImageSelectionRegion();
  if (!region || !imageEditorData) return;
  imageEditorData = readImageEditorForm();
  try {
    if (imageShotMode === 'sample') {
      imageApplySelection.disabled = true;
      imageShotStatus.textContent = 'Saving selected screenshot crop...';
      const crop = selectedImageCropDataUrl(region);
      const saved = await saveImageSample(crop, region, imageEditorData.var || 'image', imageShot?.width, imageShot?.height);
      Object.assign(imageEditorData, {
        path: saved.rel_path || saved.path,
        base_w: imageShot?.width || imageEditorData.base_w || 1920,
        base_h: imageShot?.height || imageEditorData.base_h || 1080,
        x1: saved.x1, y1: saved.y1, x2: saved.x2, y2: saved.y2,
      });
      imageShotStatus.textContent = 'Sample saved.';
      refreshImagePathList();
    } else {
      Object.assign(imageEditorData, {
        search_x1: region.x1, search_y1: region.y1, search_x2: region.x2, search_y2: region.y2,
        base_w: imageShot?.width || imageEditorData.base_w || 1920,
        base_h: imageShot?.height || imageEditorData.base_h || 1080,
        fixed: false,
      });
      imageShotStatus.textContent = 'Search area selected.';
    }
    writeImageEditorForm(imageEditorData);
    saveImageEditorData();
    imageApplySelection.disabled = false;
  } catch (err) {
    imageShotStatus.textContent = err.message || String(err);
    imageApplySelection.disabled = false;
  }
};
imageShotCanvas.addEventListener('mousedown', e => {
  if (!imageShot) return;
  e.preventDefault();
  imageDragStart = canvasPointToScreen(e);
  imageSelection = { x1: imageDragStart.x, y1: imageDragStart.y, x2: imageDragStart.x, y2: imageDragStart.y };
  imageApplySelection.disabled = true;
  drawImageShot();
});
imageShotCanvas.addEventListener('mousemove', e => {
  if (!imageShot || !imageDragStart) return;
  const pt = canvasPointToScreen(e);
  imageSelection = { x1: imageDragStart.x, y1: imageDragStart.y, x2: pt.x, y2: pt.y };
  drawImageShot();
});
imageShotCanvas.addEventListener('mouseup', e => {
  if (!imageShot || !imageDragStart) return;
  const pt = canvasPointToScreen(e);
  imageSelection = { x1: imageDragStart.x, y1: imageDragStart.y, x2: pt.x, y2: pt.y };
  imageDragStart = null;
  imageApplySelection.disabled = !currentImageSelectionRegion();
  drawImageShot();
});
imageShotCanvas.addEventListener('mouseleave', () => {
  if (!imageDragStart) return;
  imageDragStart = null;
  imageApplySelection.disabled = !currentImageSelectionRegion();
  drawImageShot();
});

if (settingsBtn && settingsPanel) settingsBtn.onclick = () => settingsPanel.classList.toggle('open');
if (settingsClose && settingsPanel) settingsClose.onclick = () => settingsPanel.classList.remove('open');
if (settingsCloseBottom && settingsPanel) settingsCloseBottom.onclick = () => settingsPanel.classList.remove('open');
if (settingsSave && settingsPanel) settingsSave.onclick = async () => { if (await saveSettingsOnly()) settingsPanel.classList.remove('open'); };

modalBackdrop.onclick = hideModals;

async function toggleRecordingFromUi() {
  if (running || recordBusy || !isRecorderTabArmed()) return;
  recordBusy = true;
  recordBtnTop && (recordBtnTop.disabled = true);
  try {
    if (!recording) {
      const target = currentPath ? currentPath : `${currentMacro || 'recorded_macro'}.macro`;
      const ok = confirm(`Recording will overwrite the current macro when stopped:\n\n${target}\n\nStart recording?`);
      if (!ok) return;
      const res = await api('/api/record/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sensitivity: sensitivity(), dashboard: true }),
      });
      if (!res.ok) { alert(res.error || 'Could not start recording.'); return; }
      await pollState();
      return;
    }

    const res = await api('/api/record/stop', { method: 'POST' });
    if (!res.ok) { alert(res.error || 'Could not stop recording.'); return; }
    applyLoadedMacro(res);
    await refreshMacroList();
    await pollState();
  } finally {
    recordBusy = false;
    if (recordBtnTop) recordBtnTop.disabled = false;
  }
}

async function toggleRecordingFromHotkey() {
  if (running || !isRecorderTabArmed()) return;
  const wasRecording = recording;
  await delay(120);
  await pollState();
  if (recording !== wasRecording) return;

  if (!wasRecording) {
    const res = await api('/api/record/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sensitivity: sensitivity(), dashboard: true }),
    });
    if (!res.ok) { alert(res.error || 'Could not start recording.'); return; }
    await pollState();
    return;
  }

  const res = await api('/api/record/stop', { method: 'POST' });
  if (!res.ok) {
    await pollState();
    return;
  }
  applyLoadedMacro(res);
  await refreshMacroList();
  await pollState();
}

recordBtnTop.onclick = toggleRecordingFromUi;

function persistPlayMode() {
  playbackRepeat();
  saveSettingsOnly({ silent: true }).catch(() => {});
}

if (playModeSelect) {
  playModeSelect.addEventListener('change', () => {
    playbackMode = playModeSelect.value || 'once';
    if (playbackMode === 'times') playbackTimesValue = clampTimes(playModeTimes ? playModeTimes.value : playbackTimesValue);
    applyPlayModeUI();
    persistPlayMode();
  });
}
if (playModeTimes) {
  playModeTimes.addEventListener('change', () => {
    playbackTimesValue = clampTimes(playModeTimes.value);
    applyPlayModeUI();
    persistPlayMode();
  });
}

playStopBtn.onclick = async () => {
  if (playBusy || !isRecorderTabArmed()) return;
  playBusy = true;
  playStopBtn && (playStopBtn.disabled = true);
  try {
    if (running) {
      await api('/api/stop', { method: 'POST' });
      await pollState();
      return;
    }
    if (recording || blocks.length === 0) return;
    const saved = await saveCurrent(undefined, undefined, { sensitivityOverride: currentMeta, reload: false });
    if (!saved || !currentPath) return;
    await api('/api/play', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: currentPath, repeat: playbackRepeat(), dashboard: true, sensitivity: sensitivity() }),
    });
    await pollState();
  } finally {
    playBusy = false;
    if (playStopBtn) playStopBtn.disabled = false;
  }
};

// ── Polling loop — updates run badge + progress bar + timer ───────────────────

function isRecorderTabArmed() {
  try {
    const frame = window.frameElement;
    if (!frame) return true;
    return frame.ownerDocument.body.classList.contains('tab-recorder');
  } catch (e) {
    return !!recorderTabArmed;
  }
}

window.addEventListener('message', e => {
  if (!e.data) return;
  if (e.data.type === 'recorder-arm') {
    recorderTabArmed = !!e.data.active;
    if (recorderTabArmed) {
      api('/api/bootstrap').then(b => {
        const bs = (b && b.sensitivity) || {};
        appUserSensitivity = {
          SENS_USER_H: Number(bs.SENS_USER_H ?? bs.user_h ?? appUserSensitivity.SENS_USER_H ?? 17),
          SENS_USER_V: Number(bs.SENS_USER_V ?? bs.user_v ?? appUserSensitivity.SENS_USER_V ?? 17),
        };
      }).catch(() => {});
    }
  }
  if (e.data.type === 'bot-config') {
    if (e.data.sensitivity) {
      const s = e.data.sensitivity;
      appUserSensitivity = {
        SENS_USER_H: Number(s.SENS_USER_H ?? s.USER_SENS_H ?? appUserSensitivity.SENS_USER_H ?? 17),
        SENS_USER_V: Number(s.SENS_USER_V ?? s.USER_SENS_V ?? appUserSensitivity.SENS_USER_V ?? 17),
      };
    }
    if (e.data.record_binding) recordBindingValue = String(e.data.record_binding).toUpperCase();
    if (e.data.play_binding) playBindingValue = String(e.data.play_binding).toUpperCase();
    if (e.data.record_binding || e.data.play_binding) renderRecorderHint();
  }
});

document.addEventListener('keydown', async e => {
  if (!isRecorderTabArmed()) return;
  const pressed = eventBinding(e);
  if (pressed === recordBindingValue) {
    e.preventDefault();
    await toggleRecordingFromHotkey();
    return;
  }
  if (pressed === playBindingValue) {
    const wasRunning = running;
    e.preventDefault();
    await delay(120);
    await pollState();
    if (running === wasRunning) await playStopBtn.onclick();
  }
});

setInterval(pollState, 200);

bootstrap().catch(e => {
  console.error(e);
  alert('Macro Engine UI failed to initialize.');
});
