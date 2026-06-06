# Инструкция по запуску бота СТЗ

## Шаг 1. Получить токен бота

1. Открой Telegram, найди **@BotFather**
2. Напиши `/newbot`
3. Придумай имя и username для бота (username должен заканчиваться на `bot`)
4. BotFather пришлёт тебе токен — длинная строка вида `123456789:AAFxxxxxx`
5. Открой файл `bot.py` и вставь токен сюда:
   ```
   BOT_TOKEN = "ВАШ_ТОКЕН_ЗДЕСЬ"
   ```

---

## Шаг 2. Запуск локально (для теста)

Открой терминал в папке с файлами и выполни по очереди:

```bash
# Установить зависимости (один раз)
pip install -r requirements.txt

# Запустить бота
python bot.py
```

Если бот запустился — в терминале появится:
```
Бот запущен. Нажми Ctrl+C для остановки.
```

Теперь найди своего бота в Telegram и напиши `/start`.

Чтобы остановить — нажми `Ctrl+C` в терминале.

---

## Шаг 3. Запуск на сервере через Docker (для друга)

Передай другу три файла: `bot.py`, `requirements.txt`, `Dockerfile`

Команды для запуска на сервере:

```bash
# Собрать контейнер
docker build -t stz-bot .

# Запустить контейнер (работает в фоне, перезапускается автоматически)
docker run -d --restart unless-stopped --name stz-bot stz-bot
```

### Полезные команды для друга:

```bash
# Посмотреть логи бота
docker logs stz-bot

# Остановить бота
docker stop stz-bot

# Перезапустить после обновления bot.py
docker stop stz-bot
docker rm stz-bot
docker build -t stz-bot .
docker run -d --restart unless-stopped --name stz-bot stz-bot
```

---

## Возможные проблемы

**`ModuleNotFoundError: No module named 'telegram'`**
→ Запусти: `pip install -r requirements.txt`

**Бот не отвечает в Telegram**
→ Проверь что токен вставлен правильно в `bot.py`
→ Убедись что бот запущен (в терминале должна быть надпись "Бот запущен")
