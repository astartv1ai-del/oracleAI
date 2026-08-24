/* DOM transport: превращает браузерные события в команды app.
 * Business/UI action mapping находится в 15-actions.js.
 */
window.app = app;


document.addEventListener('click', function (event) {
  const el = event.target && event.target.closest
    ? event.target.closest('[data-act]')
    : null;
  if (el) app.dispatchAction(el, event);
});

// Keep the hub scannable: opening one capability list closes the others.
document.addEventListener('toggle', function (event) {
  const details = event.target;
  if (!details || !details.matches || !details.matches('.agent-card__more') || !details.open) return;
  document.querySelectorAll('.agent-card__more[open]').forEach(other => {
    if (other !== details) other.open = false;
  });
});


document.addEventListener('keydown', function (event) {
  if (event.key === 'Enter' && event.target && event.target.id === 'chat-input' && !event.shiftKey) {
    event.preventDefault();
    app.doSend();
  }
});


document.addEventListener('input', function (event) {
  if (event.target && event.target.id === 'tarot-q') {
    app.pendingQ(event.target.value);
  }
  if (event.target && event.target.id === 'chat-input') {
    app.chat.draft = event.target.value;
  }
  if (event.target && event.target.id === 'workspace-history-q') {
    app.searchHistory(event.target.value);
  }
});


app.boot();
