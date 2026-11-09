// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_call_flow                          ║
// ║ Category: base/flow                            ║
// ║ Desc: "Call flow 'flow1' from state 'Start1'" ║
// ║   Calls the procedure with that ID, declared   ║
// ║   by a Procedure block in the Flow blockly.    ║
// ║   The state is the hat it lives under (shown   ║
// ║   in the picker for clarity).                  ║
// ╚══════════════════════════════════════════════╝

function _pcrFlowsList() {
  var flows = window._mfFlows || [];
  if (flows.length) return flows;
  // fallback: plain callable procs (no state context)
  return (window._pcrCallableProcs || []).map(function (p) { return { name: p, state: '' }; });
}

function _pcrFlowStateFor(name) {
  var flows = window._mfFlows || [];
  for (var i = 0; i < flows.length; i++) {
    if (flows[i] && flows[i].name === name) return flows[i].state || '';
  }
  return '';
}

Blockly.Blocks['pcr_call_flow'] = {
  init: function () {
    var self = this;
    var flowDD = new Blockly.FieldDropdown(function () {
      var flows = _pcrFlowsList();
      return flows.length ? flows.map(function (f) {
        var st = f.state ? ' (' + f.state + ')' : '';
        return [f.name + st, f.name];
      }) : [["(no flows in this mode)", ""]];
    }, function (val) {
      // picking a flow syncs the state field to where it lives
      if (val) {
        try { self.setFieldValue(_pcrFlowStateFor(val), 'STATE'); } catch (e) {}
      }
      return val;
    });
    var stateDD = new Blockly.FieldDropdown(function () {
      var nodes = window._mfFlowNodes || [];
      return nodes.length ? nodes.map(function (n) {
        return [n.label || n.id, n.id || ''];
      }) : [["(no states)", ""]];
    });
    this.appendDummyInput()
      .appendField("Call flow")
      .appendField(flowDD, "FLOW")
      .appendField("from state")
      .appendField(stateDD, "STATE");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour(120);
    this.setTooltip(
      "Calls the procedure with that ID (declared by a Procedure block in " +
      "the Flow blockly). 'from state' shows which state hat it lives " +
      "under — the name is unique, so the call always finds it."
    );
  }
};

Blockly.Python['pcr_call_flow'] = function (block) {
  var name = block.getFieldValue('FLOW');
  if (!name) return 'pass\n';
  var fn = 'proc_' + String(name).replace(/[^A-Za-z0-9_]+/g, '_')
    .replace(/^_+|_+$/g, '').replace(/^([0-9])/, '_$1');
  return fn + '()\n';
};
