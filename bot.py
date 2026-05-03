import asyncio
import logging
import os
import requests
from datetime import time
from telegram import Bot, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import pytz

# ══════════════════════════════════════════════════
# НАСТРОЙКИ
# ══════════════════════════════════════════════════
TELEGRAM_TOKEN   = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID          = os.environ.get("CHAT_ID")
OPENROUTER_KEY   = os.environ.get("OPENROUTER_API_KEY")

BISHKEK = pytz.timezone("Asia/Bishkek")

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# ══════════════════════════════════════════════════
# ПОДПИСЧИКИ
# ══════════════════════════════════════════════════
subscribers: set = set()
chat_histories: dict = {}

# ══════════════════════════════════════════════════
# КЛАВИАТУРА
# ══════════════════════════════════════════════════
MENU = ReplyKeyboardMarkup(
    [
        [KeyboardButton("🌸 Аффирмации"),   KeyboardButton("🎤 Голос")],
        [KeyboardButton("🎙️ Риторика"),     KeyboardButton("🃏 Карта дня")],
        [KeyboardButton("🇰🇬 Кыргызский"),  KeyboardButton("✨ Всё сразу")],
    ],
    resize_keyboard=True,
    persistent=True,
)

# ══════════════════════════════════════════════════
# ЗАПРОС К AI
# ══════════════════════════════════════════════════
def ask_claude(system: str, user: str, max_tokens: int = 700) -> str:
    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "anthropic/claude-sonnet-4-5",
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
        },
        timeout=60,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()

# ══════════════════════════════════════════════════
# ГЕНЕРАТОРЫ
# ══════════════════════════════════════════════════
def gen_affirmations() -> str:
    text = ask_claude(
        system="Ты коуч по аффирмациям. Пишешь по-русски. Создавай вдохновляющие аффирмации от первого лица «Я...».",
        user="Создай 5 мощных аффирмаций на сегодня. Темы: уверенность в себе, красивый голос, развитие, женственность, внутренняя сила. Каждую с новой строки. Без нумерации. Добавь одну мотивирующую фразу в конце.",
        max_tokens=500,
    )
    return f"🌸 *Аффирмации на сегодня*\n\n{text}"

def gen_voice_exercise() -> str:
    exercises = [
        ("Дыхательная разминка", "диафрагмальное дыхание, опора голоса"),
        ("Резонаторы и гудение", "вибрация в груди и носу, глубина тембра"),
        ("Дикция — скороговорки", "чёткость согласных, темп, артикуляция"),
        ("Интонация и пауза", "выразительность, управление паузой"),
        ("Снятие зажимов", "расслабление гортани, свобода звука"),
        ("Тембр и окраска голоса", "эмоциональная окраска, цвет голоса"),
        ("Работа с текстом вслух", "чтение с выражением, акценты"),
    ]
    import datetime
    day = datetime.date.today().timetuple().tm_yday
    ex_name, ex_focus = exercises[day % len(exercises)]
    text = ask_claude(
        system="Ты педагог по постановке голоса. Пишешь по-русски, тепло и практично.",
        user=f"Напиши упражнение на тему «{ex_name}» (фокус: {ex_focus}). Структура: зачем (1 предложение), пошаговая инструкция (4-5 шагов), совет дня. Без лишних вступлений.",
        max_tokens=600,
    )
    return f"🎤 *Упражнение для голоса — {ex_name}*\n\n{text}"

def gen_rhetoric() -> str:
    techniques = [
        "Принцип трёх — три аргумента звучат убедительнее одного",
        "Сила паузы — пауза перед важной мыслью создаёт акцент",
        "Метод PREP — Position, Reason, Example, Position",
        "Анафора — повтор в начале фраз создаёт ритм",
        "Сторителлинг — история убеждает лучше аргумента",
        "Антитеза — противопоставление делает фразу запоминаемой",
        "Зрительный контакт — 3-5 секунд на одного человека",
        "Конкретика вместо абстракций — цифры и детали",
        "Структура речи: скажи — скажи — скажи что сказала",
        "Градация — нарастание напряжения к главной мысли",
        "Риторический вопрос — вовлекает и заставляет думать",
        "Эффект начала и конца — аудитория помнит первое и последнее",
        "Метафора — образ запоминается лучше объяснения",
        "Активный залог — говори «я сделала», не «было сделано»",
    ]
    import datetime
    day = datetime.date.today().timetuple().tm_yday
    technique = techniques[day % len(techniques)]
    text = ask_claude(
        system="Ты тренер по риторике. Пишешь по-русски, живо и практично.",
        user=f"Объясни технику: «{technique}». Структура: суть (2-3 предложения), пример (конкретная фраза), мини-задание на сегодня. Без лишних вступлений.",
        max_tokens=500,
    )
    return f"🎙️ *Техника риторики дня*\n\n{text}"

def gen_meta_card() -> str:
    cards = [
        ("🌊 Течение", "Куда ведёт тебя твоё течение прямо сейчас?"),
        ("🌸 Расцвет", "Что в тебе сейчас раскрывается и хочет расцвести?"),
        ("🔥 Огонь", "Что зажигает тебя изнутри?"),
        ("🌙 Луна", "Что скрыто в тени, о чём ты ещё не готова говорить?"),
        ("🦋 Трансформация", "Через какую трансформацию ты сейчас проходишь?"),
        ("🌿 Корни", "Что даёт тебе силу и почву под ногами?"),
        ("⭐ Путеводная звезда", "Какая твоя настоящая мечта — та, что шепчет в тишине?"),
        ("🪞 Зеркало", "Что ты видишь, когда честно смотришь внутрь себя?"),
        ("🌈 После бури", "Что появится в твоей жизни после нынешнего периода?"),
        ("🗝️ Ключ", "Какая дверь ждёт, когда ты решишься её открыть?"),
        ("🕊️ Свобода", "От чего нужно отпустить, чтобы почувствовать свободу?"),
        ("💎 Ценность", "Что в тебе есть ценного, что ты пока не замечаешь?"),
    ]
    import datetime
    day = datetime.date.today().timetuple().tm_yday
    card_name, card_question = cards[day % len(cards)]
    text = ask_claude(
        system="Ты проводник по метафорическим картам. Пишешь по-русски, поэтично и глубоко.",
        user=f"Карта дня: {card_name}. Вопрос: {card_question}. Дай: интерпретацию (3-4 предложения), вопрос для размышления, аффирмацию связанную с картой.",
        max_tokens=500,
    )
    return f"🃏 *Карта дня — {card_name}*\n\n_{card_question}_\n\n{text}"

def gen_kyrgyz() -> str:
    words = [
        ("Жүрөк", "[zhürök]", "Сердце / Душа", "Жүрөгүм сени сагынат — Моё сердце скучает по тебе"),
        ("Жарык", "[zharïk]", "Свет / Светлый", "Жарык дүйнө — Светлый мир"),
        ("Сүйүү", "[süyüü]", "Любовь", "Мен сени сүйөм — Я тебя люблю"),
        ("Кооз", "[kooz]", "Красивый", "Сен абдан кооз сың — Ты очень красивая"),
        ("Ырыс", "[ïrïs]", "Счастье", "Ырыс алды ынтымак — Счастье начинается с согласия"),
        ("Тынчтык", "[tïnchtïk]", "Мир / Покой", "Тынчтык болсун — Пусть будет мир"),
        ("Умут", "[umut]", "Надежда", "Умут менен жашайм — Живу с надеждой"),
        ("Жаңы", "[zhanï]", "Новый", "Жаңы башталыш — Новое начало"),
        ("Кудурет", "[kudüret]", "Сила", "Анын кудурети чоң — Её сила велика"),
        ("Ак жол", "[ak zhol]", "Счастливого пути", "Ак жол! — Счастливого пути!"),
        ("Ысык", "[ïsïk]", "Тёплый", "Ысык жүрөк — Тёплое сердце"),
        ("Сулуу", "[suluu]", "Красивая", "Сен абдан сулуусуң — Ты очень красивая"),
        ("Бакыт", "[bakït]", "Счастье", "Бакытты издейм — Ищу счастье"),
        ("Жылуу", "[zhïluu]", "Тёплый (о чувствах)", "Жылуу сөздөр — Тёплые слова"),
    ]
    import datetime
    day = datetime.date.today().timetuple().tm_yday
    word, transcription, meaning, example = words[day % len(words)]
    text = ask_claude(
        system="Ты репетитор по кыргызскому языку. Пишешь по-русски, тепло и с юмором.",
        user=f"Слово дня: «{word}» {transcription} — {meaning}. Напиши: интересный факт (1-2 предложения), 2 примера (кыргызский + перевод), мини-задание.",
        max_tokens=500,
    )
    return f"🇰🇬 *Кыргызское слово дня*\n\n*{word}* {transcription}\n_{meaning}_\n\n📝 _{example}_\n\n{text}"

# ══════════════════════════════════════════════════
# РАССЫЛКА
# ══════════════════════════════════════════════════
async def broadcast(bot: Bot, text: str):
    all_users = subscribers | {CHAT_ID}
    for uid in all_users:
        try:
            await bot.send_message(chat_id=uid, text=text, parse_mode="Markdown")
        except Exception as e:
            log.warning(f"Не удалось отправить {uid}: {e}")

async def job_affirmations(context: ContextTypes.DEFAULT_TYPE):
    await broadcast(context.bot, gen_affirmations())

async def job_voice(context: ContextTypes.DEFAULT_TYPE):
    await broadcast(context.bot, gen_voice_exercise())

async def job_rhetoric(context: ContextTypes.DEFAULT_TYPE):
    await broadcast(context.bot, gen_rhetoric())

async def job_card(context: ContextTypes.DEFAULT_TYPE):
    await broadcast(context.bot, gen_meta_card())

async def job_kyrgyz(context: ContextTypes.DEFAULT_TYPE):
    await broadcast(context.bot, gen_kyrgyz())

# ══════════════════════════════════════════════════
# КОМАНДЫ
# ══════════════════════════════════════════════════
async def cmd_start(update, context):
    uid = update.effective_chat.id
    subscribers.add(uid)
    name = update.effective_user.first_name or "друг"
    await update.message.reply_text(
        f"🌸 Привет, {name}! Я твой помощник по развитию.\n\n"
        "Каждый день буду присылать:\n"
        "• 09:00 — Аффирмации 🌸\n"
        "• 10:00 — Голос 🎤\n"
        "• 10:01 — Кыргызский 🇰🇬\n"
        "• 11:00 — Риторика 🎙️\n"
        "• 12:00 — Карта дня 🃏\n\n"
        "Или нажми кнопку внизу 👇",
        reply_markup=MENU,
    )

async def cmd_stop(update, context):
    uid = update.effective_chat.id
    subscribers.discard(uid)
    await update.message.reply_text("Ты отписалась. Напиши /start чтобы подписаться снова.")

# ══════════════════════════════════════════════════
# ОБРАБОТЧИК ВСЕХ СООБЩЕНИЙ
# ══════════════════════════════════════════════════
async def handle_message(update, context):
    uid = update.effective_chat.id
    name = update.effective_user.first_name or "друг"
    text = update.message.text

    # Кнопки меню
    if text == "🌸 Аффирмации":
        await update.message.reply_text(gen_affirmations(), parse_mode="Markdown", reply_markup=MENU)
        return
    if text == "🎤 Голос":
        await update.message.reply_text(gen_voice_exercise(), parse_mode="Markdown", reply_markup=MENU)
        return
    if text == "🎙️ Риторика":
        await update.message.reply_text(gen_rhetoric(), parse_mode="Markdown", reply_markup=MENU)
        return
    if text == "🃏 Карта дня":
        await update.message.reply_text(gen_meta_card(), parse_mode="Markdown", reply_markup=MENU)
        return
    if text == "🇰🇬 Кыргызский":
        await update.message.reply_text(gen_kyrgyz(), parse_mode="Markdown", reply_markup=MENU)
        return
    if text == "✨ Всё сразу":
        for fn in [gen_affirmations, gen_voice_exercise, gen_rhetoric, gen_meta_card, gen_kyrgyz]:
            await update.message.reply_text(fn(), parse_mode="Markdown")
            await asyncio.sleep(1)
        return

    # Свободный чат с AI
    if uid not in chat_histories:
        chat_histories[uid] = []

    chat_histories[uid].append({"role": "user", "content": text})

    if len(chat_histories[uid]) > 20:
        chat_histories[uid] = chat_histories[uid][-20:]

    await context.bot.send_chat_action(chat_id=uid, action="typing")

    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "anthropic/claude-sonnet-4-5",
                "max_tokens": 700,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            f"Ты личный помощник и коуч по саморазвитию. "
                            f"Ты общаешься с {name}. "
                            "Помогаешь с: голосом, риторикой, аффирмациями, "
                            "кыргызским языком, личными границами и саморазвитием. "
                            "Отвечай по-русски, тепло и по делу."
                        )
                    }
                ] + chat_histories[uid],
            },
            timeout=60,
        )
        response.raise_for_status()
        reply = response.json()["choices"][0]["message"]["content"].strip()
        chat_histories[uid].append({"role": "assistant", "content": reply})
        await update.message.reply_text(reply, reply_markup=MENU)
    except Exception as e:
        log.error(f"Chat error: {e}")
        await update.message.reply_text("Что-то пошло не так, попробуй ещё раз 🙏", reply_markup=MENU)

# ══════════════════════════════════════════════════
# ЗАПУСК
# ══════════════════════════════════════════════════
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("stop",  cmd_stop))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.job_queue.run_daily(job_affirmations, time=time(9,  0, tzinfo=BISHKEK))
    app.job_queue.run_daily(job_voice,        time=time(10, 0, tzinfo=BISHKEK))
    app.job_queue.run_daily(job_kyrgyz,       time=time(10, 1, tzinfo=BISHKEK))
    app.job_queue.run_daily(job_rhetoric,     time=time(11, 0, tzinfo=BISHKEK))
    app.job_queue.run_daily(job_card,         time=time(12, 0, tzinfo=BISHKEK))

    log.info("Бот запущен ✅")
    app.run_polling()

if __name__ == "__main__":
    main()




