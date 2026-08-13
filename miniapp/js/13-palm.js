(function () {
  'use strict';

  const palmGuide = () => `
    <div class="palm-guide" role="note">
      <b>Как снять ладонь</b>
      <span>Одна ладонь целиком, ровный свет, камера сверху, пальцы расслаблены и слегка раздвинуты. Без фильтров и бликов.</span>
    </div>`;

  app.featurePalm = function () {
    if (this.chat.pending && this.chat.pending.kind === 'palm') return;
    this.chat.pending = { kind: 'palm', loading: false, html: app.palmPickerHtml() };
    this.renderChat(document.getElementById('app-main'));
  };

  app.palmPickerHtml = function () {
    return `<section class="palm-result" aria-live="polite">
      <div class="w-title">✋ Чтение ладони</div>
      <p class="w-sub">Я опишу только то, что действительно видно на фото, и превращу символы в вопросы к себе.</p>
      ${palmGuide()}
      <label class="palm-upload" for="palm-file">
        <span class="palm-upload__icon" aria-hidden="true">＋</span>
        <b>Выбрать фото ладони</b>
        <small>JPEG, PNG или WebP · до 8 МБ</small>
      </label>
      <input id="palm-file" class="sr-only" type="file" accept="image/jpeg,image/png,image/webp" data-palm-input>
      <p class="palm-disclaimer">Это символическое чтение для саморефлексии, не медицинская диагностика и не предсказание.</p>
    </section>`;
  };

  app.palmLoadingHtml = function () {
    return `<section class="palm-result" role="status" aria-live="polite">
      <div class="w-title">✋ Смотрю на линии</div>
      <div class="palm-loading"><span></span><span></span><span></span></div>
      <p class="w-sub">Проверяю качество кадра и отделяю наблюдаемое от интерпретации…</p>
    </section>`;
  };

  function textFromResult(result) {
    const obs = Array.isArray(result.observations) ? result.observations : [];
    if (!obs.length) return '<p class="palm-muted">На этом кадре пока недостаточно деталей для уверенного чтения.</p>';
    return obs.slice(0, 6).map(item => `
      <div class="palm-observation">
        <div><b>${esc(item.topic || 'Наблюдение')}</b><span>${esc(item.visibility || 'неясно')} · ${Math.round(Number(item.confidence || 0) * 100)}%</span></div>
        <p>${esc(item.summary || 'Описание отсутствует')}</p>
      </div>`).join('');
  }

  app.palmHtml = function (result) {
    const q = result.image_quality || {};
    const needs = result.status === 'needs_photo';
    const limitations = Array.isArray(result.limitations) ? result.limitations : [];
    const prompts = Array.isArray(result.interpretive_prompts) ? result.interpretive_prompts : [];
    return `<section class="palm-result" aria-live="polite">
      <div class="w-title">✋ ${needs ? 'Нужен более ясный кадр' : 'Что видно на ладони'}</div>
      <div class="palm-quality"><b>Качество кадра</b><span>${Math.round(Number(q.score || 0) * 100)}%</span></div>
      ${textFromResult(result)}
      ${limitations.length ? `<div class="palm-limitations"><b>Границы чтения</b><p>${limitations.map(esc).join('<br>')}</p></div>` : ''}
      ${prompts.length ? `<div class="palm-prompts"><b>Вопросы к себе</b>${prompts.slice(0, 3).map(p => `<p>“${esc(p)}”</p>`).join('')}</div>` : ''}
      <p class="palm-disclaimer">Линия жизни не показывает продолжительность жизни. Это символическая рефлексия, а не диагноз и не гарантия событий.</p>
      <div class="palm-actions">
        ${needs ? '<button class="btn btn-ghost" data-act="tool-fn" data-fn="featurePalm">Переснять фото</button>' : '<button class="btn btn-primary" data-act="fill" data-val="Прочитай мою ладонь по последнему фото.">Спросить Хироманта</button>'}
      </div>
    </section>`;
  };

  async function upload(file) {
    if (!file) return;
    if (file.size > 8 * 1024 * 1024) {
      app.chat.pending = { kind: 'palm', loading: false, html: `<section class="palm-result"><div class="w-title">✋ Фото слишком большое</div><p class="palm-muted">Выбери изображение до 8 МБ.</p><button class="btn btn-ghost" data-act="tool-fn" data-fn="featurePalm">Попробовать снова</button></section>` };
      app.renderChat(document.getElementById('app-main'));
      return;
    }
    const key = app.chat.key, view = app.view;
    const pend = app.chat.pending = { kind: 'palm', loading: true, html: app.palmLoadingHtml() };
    app.renderChat(document.getElementById('app-main'));
    try {
      const response = await fetch('/api/palm' + (new URLSearchParams(location.search).get('dev_user') ? '?dev_user=' + new URLSearchParams(location.search).get('dev_user') : ''), {
        method: 'POST',
        headers: Object.assign({ 'Content-Type': file.type }, (tg() && tg().initData) ? { 'X-Init-Data': tg().initData } : {}),
        body: file,
      });
      let body = null;
      try { body = await response.json(); } catch (e) {}
      if (!response.ok) throw new Error((body && body.detail) || 'Не удалось прочитать фото');
      if (!widAlive(key, view, pend)) return;
      app.chat.pending = { kind: 'palm', loading: false, html: app.palmHtml(body) };
      haptic('success');
    } catch (e) {
      if (!widAlive(key, view, pend)) return;
      app.chat.pending = { kind: 'palm', loading: false, html: `<section class="palm-result"><div class="w-title">✋ Не получилось прочитать фото</div><p class="palm-muted">${esc(e.message || 'Попробуй ещё раз')}</p>${palmGuide()}<button class="btn btn-ghost" data-act="tool-fn" data-fn="featurePalm">Попробовать снова</button></section>` };
      haptic('error');
    }
    app.renderChat(document.getElementById('app-main'));
  }

  document.addEventListener('change', e => {
    const input = e.target && e.target.matches && e.target.matches('[data-palm-input]') ? e.target : null;
    if (input && input.files && input.files[0]) upload(input.files[0]);
  });
}());
