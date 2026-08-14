/* UI command registry.
 * Views expose methods on `app`; this module owns only the mapping from
 * declarative data-act attributes to those methods.
 */
(function () {
  'use strict';

  const call = (name, ...args) => {
    if (typeof app[name] === 'function') app[name](...args);
  };

  app.dispatchAction = function (el) {
    const action = el && el.dataset && el.dataset.act;
    const handler = actionHandlers[action];
    if (handler) handler(el, el.dataset);
  };

  const actionHandlers = {
    go: (el, data) => call('go', data.goto),
    chat: (el, data) => call('openChat', data.chat),
    'chat-fn': (el, data) => {
      call('setToolbox', false);
      call('openChat', data.chat, () => call(data.fn));
    },
    back: () => call('closeChat'),
    clear: () => call('clearThread'),
    feature: (el, data) => { tactile('select'); call(data.fn); },
    'tool-fn': (el, data) => {
      tactile('open');
      call(data.fn);
    },
    'tool-toggle': () => { tactile('open'); call('toggleToolbox'); },
    'palm-start': () => { tactile('select'); call('featurePalm'); },
    'today-ask': () => call('todayAsk'),
    'day-flip': () => call('todayFlip'),
    'matrix-node': (el, data) => call('selectMatrixNode', data.key),
    'matrix-ask': (el, data) => call('matrixAsk', data.key),
    'moon-expand': (el, data) => call('expandMoonDay', parseInt(data.i, 10)),
    'p-action': (el, data) => call('practiceAction', data.code, data.a),
    'diary-add': () => call('diaryAdd'),
    'diary-mood': (el, data) => call('setDiaryMood', data.mood),
    'diary-summary': () => call('diarySummary'),
    'career-day': (el, data) => call('careerDay', parseInt(data.i, 10)),
    'career-ask': () => call('careerAsk'),
    sessions: () => call('toggleSessions'),
    moon: () => call('openMoon'),
    'moon-week': () => call('toggleMoonWeek'),
    'moon-day': (el, data) => call('toggleMoonDay', parseInt(data.i, 10)),
    ptab: (el, data) => call('switchPTab', data.tab),
    'new-session': () => call('newSession'),
    'open-session': (el, data) => call('openSession', parseInt(data.tid, 10)),
    'del-session': (el, data) => call('delSession', parseInt(data.tid, 10)),
    send: (el, data) => call('doSend', data.val || undefined),
    'retry-chat': () => call('loadThread', app.chat.key),
    fill: (el, data) => call('fillInput', data.val),
    memories: () => call('openMemories'),
    'toggle-memory': () => call('toggleMemory'),
    'full-chart': () => call('openFullChart'),
    'fc-explain': () => call('explainChart'),
    'del-mem': (el, data) => call('delMem', parseInt(data.id, 10)),
    'add-mem': () => call('addMem'),
    'pick-open': () => call('openSpreadPicker'),
    'pick-choose': (el, data) => call('chooseSpread', data.code),
    draw: () => call('doDraw'),
    'tarot-question': (el, data) => call('setTarotQuestion', data.value),
    flip: (el, data) => call('flipCard', parseInt(data.i, 10)),
    'flip-card': (el) => call('flipDayCard', el),
    interpret: () => call('doInterpret'),
    compat: () => call('doCompat'),
    'compat-rel': (el, data) => call('setCompatRel', data.rel),
    sphere: (el, data) => call('selectSphere', parseInt(data.sphere, 10)),
    'spd-toggle': () => call('toggleSpdAnswer'),
    planet: (el, data) => call('selectPlanet', parseInt(data.p, 10)),
    'el-filter': (el, data) => call('filterElement', data.el),
    reading: (el, data) => call('openReading', parseInt(data.id, 10)),
    'share-reading': (el, data) => call('shareReading', parseInt(data.id, 10)),
    outcome: (el, data) => call('setOutcome', parseInt(data.id, 10), data.val),
    'ref-copy': () => call('refCopy'),
    report: (el, data) => call('openReport', data.kind),
    build: () => call('doBuildChart'),
    ask: (el, data) => call('askAgent', data.chat, data.q),
    'all-readings': () => call('openAllReadings'),
    bell: () => call('openBell'),
    gender: () => call('openGender'),
    'set-gender': (el, data) => call('setGender', data.gender),
    language: () => call('openLanguage'),
    'set-lang': (el, data) => call('setLanguage', data.lang),
    'ask-chart': () => call('askChart'),
    'share-chart': () => call('shareChart'),
    'share-compat': (el, data) => call('shareCompat', data.pdate, data.pname, data.rel),
    'modal-close': () => call('closeModal')
  };

  app.actionHandlers = actionHandlers;
}());
