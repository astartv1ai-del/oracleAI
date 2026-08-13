(function () {
  'use strict';

  const PALM_TOPICS = {
    heart_line: 'Линия сердца', head_line: 'Линия головы', life_line: 'Линия жизни',
    fate_line: 'Линия судьбы', sun_line: 'Линия Солнца', relationship_line: 'Линии отношений',
    mount_venus: 'Холм Венеры', mount_moon: 'Холм Луны', fingers: 'Пальцы', unknown: 'Наблюдение'
  };
  const VISIBILITY = { clear: 'видно', partial: 'частично', unclear: 'неясно', not_visible: 'не видно' };
  const palmGuide = () => `
    <div class="palm-guide" role="note">
      <b>Снимок, который поможет</b>
      <span>Одна ладонь целиком · ровный свет · камера сверху · пальцы расслаблены. Без фильтров, бликов и украшений.</span>
      <div class="palm-guide__steps"><i>1</i><i>2</i><i>3</i><small>целиком</small><small>без бликов</small><small>пальцы свободны</small></div>
    </div>`;

  app.featurePalm = function () {
    if (this.chat.pending && this.chat.pending.kind === 'palm') return;
    this.chat.pending = { kind: 'palm', loading: false, html: app.palmPickerHtml() };
    this.renderChat(document.getElementById('app-main'));
  };

  app.palmPickerHtml = function () {
    const preview = this._palmPreview ? `<div class="palm-preview"><img src="${esc(this._palmPreview)}" alt="Предпросмотр выбранной ладони"><button type="button" class="palm-preview__clear" data-act="tool-fn" data-fn="featurePalm">Изменить</button></div>` : '';
    return `<section class="palm-result" aria-live="polite">
      <div class="w-title">✋ Чтение ладони</div>
      <p class="w-sub">Я опишу только то, что действительно видно на фото, и превращу символы в вопросы к себе.</p>
      ${preview}
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
    const preview = this._palmPreview ? `<div class="palm-preview palm-preview--loading"><img src="${esc(this._palmPreview)}" alt="Загруженная ладонь"><span>◌</span></div>` : '';
    return `<section class="palm-result" role="status" aria-live="polite">
      <div class="w-title">✋ Смотрю на линии</div>
      ${preview}
      <div class="palm-progress"><span class="is-on">Фото</span><i></i><span class="is-on">Качество</span><i></i><span>Наблюдения</span></div>
      <div class="palm-loading"><span></span><span></span><span></span></div>
      <p class="w-sub">Проверяю качество кадра и отделяю наблюдаемое от интерпретации…</p>
    </section>`;
  };

  function textFromResult(result) {
    const obs = Array.isArray(result.observations) ? result.observations : [];
    if (!obs.length) return '<p class="palm-muted">На этом кадре пока недостаточно деталей для уверенного чтения.</p>';
    return obs.slice(0, 6).map(item => {
      const topic = PALM_TOPICS[item.topic] || item.topic || 'Наблюдение';
      const visibility = VISIBILITY[item.visibility] || 'неясно';
      const confidence = Math.round(Number(item.confidence || 0) * 100);
      return `
      <div class="palm-observation">
        <div><b>${esc(topic)}</b><span>${esc(visibility)} · ${confidence}%</span></div>
        <div class="palm-confidence"><i style="width:${confidence}%"></i></div>
        <p>${esc(item.summary || 'Описание отсутствует')}</p>
      </div>`;
    }).join('');
  }

  app.palmHtml = function (result) {
    const q = result.image_quality || {};
    const needs = result.status === 'needs_photo';
    const limitations = Array.isArray(result.limitations) ? result.limitations : [];
    const prompts = Array.isArray(result.interpretive_prompts) ? result.interpretive_prompts : [];
    return `<section class="palm-result" aria-live="polite">
      <div class="w-title">✋ ${needs ? 'Нужен более ясный кадр' : 'Что видно на ладони'}</div>
      <div class="palm-quality" style="--quality:${Math.round(Number(q.score || 0) * 100)}"><b>Качество кадра</b><span>${Math.round(Number(q.score || 0) * 100)}%</span></div>
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
    try { app._palmPreview = URL.createObjectURL(file); } catch (e) { app._palmPreview = ''; }
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
