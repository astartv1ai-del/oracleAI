@router.message(PalmUpload.photo, F.photo)
async def palm_photo(message: Message, state: FSMContext, db):
    user = await users.get(db, message.from_user.id)
    status = await begin_status(message, user, BotStage.USING_TOOL,
                                "Мира проверяет качество снимка…" if user["lang"] != "en" else "Mira is checking the photo quality…")
    buf = BytesIO()
    try:
        await message.bot.download(message.photo[-1].file_id, destination=buf)
        result = await palm_core.analyze_and_save(db, user, buf.getvalue(), surface="bot")
    except ValueError as exc:
        await status.set(BotStage.RECOVERABLE_ERROR,
                         "Try a clearer photo" if user["lang"] == "en"
                         else "Проверь кадр и попробуй снова")
        await message.answer(
            f"✋ Не получилось подготовить снимок: {tg_esc(str(exc))}\n\n"
            "Попробуй фото одной ладони целиком при ровном свете.", reply_markup=back_menu())
        return
    except Exception as exc:  # noqa: BLE001
        log.warning("palm photo analysis failed: %s", exc)
        await status.set(BotStage.RECOVERABLE_ERROR, "Try a clearer photo" if user["lang"] == "en" else "Попробуй более чёткий снимок")
        await message.answer("✋ Mira could not finish this reading. Try one clear photo of the whole palm." if user["lang"] == "en" else "✋ Мира пока не смогла завершить чтение. Попробуй ещё раз с более чётким снимком.",
                             reply_markup=back_menu())
        return
    await status.set(BotStage.SUCCESS)
    observations = result.get("observations") or []
    narrative = (result.get("narrative") or "").strip()
    prompts = result.get("interpretive_prompts") or []
    reflection = f"\n\n<b>Вопрос к себе</b>\n{tg_esc(str(prompts[0]))}" if prompts else ""
    safety = "\n\n<i>Это описание видимого в кадре, не диагноз и не прогноз.</i>"
    if result.get("status") == "needs_photo":
        limits = "\n".join(f"• {tg_esc(str(item))}" for item in (result.get("limitations") or [])[:3])
        if narrative:
            text = f"✋ <b>Мира · Карта наблюдений</b>\n\n{tg_esc(narrative)}\n\n<b>Нужен дополнительный кадр</b>\n{limits}{reflection}{safety}"
        else:
            text = f"✋ <b>Мире нужен более ясный кадр</b>\n\n{limits or 'Пересними ладонь целиком при ровном свете.'}{safety}"
    else:
        if narrative:
            text = f"✋ <b>Мира · Карта наблюдений</b>\n\n{tg_esc(narrative)}{reflection}{safety}"
        else:
            rows = []
            for item in observations[:4]:
                label = PALM_TOPIC_LABELS.get(str(item.get("topic") or ""), "Наблюдение")
                confidence = int(round(float(item.get("confidence") or 0) * 100))
                rows.append(f"• <b>{tg_esc(label)}</b> · {confidence}%\n{tg_esc(str(item.get('summary') or 'без описания'))}")
            text = (f"✋ <b>Карта видимых зон от Миры</b>\n\n" +
                    "\n\n".join(rows) + reflection + safety)
    await state.clear()
    await message.answer(text, reply_markup=back_menu())
