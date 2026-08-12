/* events: экспорт app + делегирование click/keydown/input + boot */
window.app = app;

/* ── прод-CSP: вместо inline onclick/oninput/onkeydown — делегирование ──
   data-act на элементе + один обработчик на документе. Вложенные [data-act]
   (чип внутри карточки) берёт ближайший — отдельный stopPropagation не нужен. */

document.addEventListener('click', e => {
  const el = e.target && e.target.closest ? e.target.closest('[data-act]') : null;
  if (!el) return;
  const act = el.dataset.act, v = el.dataset;
  switch (act) {
    case 'go': app.go(v.goto); break;
    case 'chat': app.openChat(v.chat); break;
    case 'chat-fn':
      app.setToolbox(false);
      app.openChat(v.chat, () => app[v.fn] && app[v.fn]());
      break;
    case 'back': app.closeChat(); break;
    case 'clear': app.clearThread(); break;
    case 'feature': haptic('light'); app[v.fn] && app[v.fn](); break;
    case 'tool-fn':
      haptic('light');
      vb(15);
      app[v.fn] && app[v.fn]();
      break;
    case 'tool-toggle': app.toggleToolbox(); break;
    case 'today-ask': app.todayAsk(); break;
    case 'day-flip': app.todayFlip(); break;
    case 'matrix-node': app.selectMatrixNode(v.key); break;
    case 'matrix-ask': app.matrixAsk(v.key); break;
    case 'moon-expand': app.expandMoonDay(parseInt(v.i, 10)); break;
    case 'p-action': app.practiceAction(v.code, v.a); break;
    case 'diary-add': app.diaryAdd(); break;
    case 'diary-summary': app.diarySummary(); break;
    case 'career-day': app.careerDay(parseInt(v.i, 10)); break;
    case 'career-ask': app.careerAsk(); break;
    case 'sessions': app.toggleSessions(); break;
    case 'moon': app.openMoon(); break;
    case 'moon-week': app.toggleMoonWeek(); break;
    case 'moon-day': app.toggleMoonDay(parseInt(v.i, 10)); break;
    case 'ptab': app.switchPTab(v.tab); break;
    case 'new-session': app.newSession(); break;
    case 'open-session': app.openSession(parseInt(v.tid, 10)); break;
    case 'del-session': app.delSession(parseInt(v.tid, 10)); break;
    case 'send': app.doSend(v.val || undefined); break;
    case 'fill': app.fillInput(v.val); break;
    case 'memories': app.openMemories(); break;
    case 'full-chart': app.openFullChart(); break;
    case 'fc-explain': app.explainChart(); break;
    case 'del-mem': app.delMem(parseInt(v.id, 10)); break;
    case 'add-mem': app.addMem(); break;
    case 'pick-open': app.openSpreadPicker(); break;
    case 'pick-choose': app.chooseSpread(v.code); break;
    case 'draw': app.doDraw(); break;
    case 'flip': app.flipCard(parseInt(v.i, 10)); break;
    case 'flip-card': app.flipDayCard(el); break;
    case 'interpret': app.doInterpret(); break;
    case 'compat': app.doCompat(); break;
    case 'compat-rel': app.setCompatRel(v.rel); break;
    case 'sphere': app.selectSphere(parseInt(v.sphere, 10)); break;
    case 'spd-toggle': app.toggleSpdAnswer(); break;
    case 'planet': app.selectPlanet(parseInt(v.p, 10)); break;
    case 'el-filter': app.filterElement(v.el); break;
    case 'reading': app.openReading(parseInt(v.id, 10)); break;
    case 'share-reading': app.shareReading(parseInt(v.id, 10)); break;
    case 'outcome': app.setOutcome(parseInt(v.id, 10), v.val); break;
    case 'ref-copy': app.refCopy(); break;
    case 'report': app.openReport(v.kind); break;
    case 'build': app.doBuildChart(); break;
    case 'ask': app.askAgent(v.chat, v.q); break;
    case 'all-readings': app.openAllReadings(); break;
    case 'bell': app.openBell(); break;
    case 'ask-chart': app.askChart(); break;
    case 'share-chart': app.shareChart(); break;
    case 'share-compat': app.shareCompat(v.pdate, v.pname, v.rel); break;
    case 'modal-close': app.closeModal(); break;
  }
});

document.addEventListener('keydown', e => {
  if (e.key === 'Enter' && e.target && e.target.id === 'chat-input') app.doSend();
});

document.addEventListener('input', e => {
  if (e.target && e.target.id === 'tarot-q') app.pendingQ(e.target.value);
  if (e.target && e.target.id === 'chat-input') app.chat.draft = e.target.value;  // G001 черновик
});


app.boot();
