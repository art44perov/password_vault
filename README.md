# 🔐 Password Vault Pro

## Русский

### Описание

**Password Vault Pro** — это современный локальный менеджер паролей и секретных данных, разработанный на Python и Flask.

Приложение позволяет безопасно хранить:

* Логины и пароли
* API-ключи
* Токены доступа
* Серверные учетные данные
* Конфиденциальные заметки
* Документы и секретную информацию

Все данные хранятся локально на компьютере пользователя и шифруются перед записью в базу данных.

---

## Основные возможности

### Безопасность

* Мастер-пароль для входа
* Шифрование AES-256
* PBKDF2 для генерации ключей
* Отсутствие хранения мастер-пароля
* Автоматическая блокировка хранилища
* Полностью локальная работа
* Работа без подключения к Интернету

### Управление записями

* Создание записей
* Редактирование записей
* Удаление записей
* Архивация записей
* Избранное
* Цветовые метки карточек
* Теги и категории

### Генератор паролей

Настраиваемые параметры:

* Длина от 8 до 64 символов
* Спецсимволы
* Цифры
* Заглавные буквы
* Исключение похожих символов

### Поиск и фильтрация

* Мгновенный поиск
* Фильтр по категориям
* Фильтр по тегам
* Фильтр по избранному
* Фильтр по дате изменения

### Резервное копирование

Экспорт:

* JSON
* CSV

Импорт:

* JSON
* CSV

Создание и восстановление резервных копий.

### Интерфейс

* Темная тема
* Glassmorphism дизайн
* Адаптивная верстка
* Современный интерфейс
* Плавные анимации
* Toast-уведомления
* Dashboard со статистикой

---

## Технологии

### Backend

* Python 3.13+
* Flask
* SQLAlchemy
* SQLite
* Cryptography

### Frontend

* HTML5
* CSS3
* JavaScript
* Bootstrap 5
* Font Awesome

---

## Структура проекта

```text
password_vault/
│
├── app.py
├── models.py
├── crypto.py
├── database.py
├── auth.py
├── backup.py
├── requirements.txt
│
├── templates/
├── static/
│   ├── css/
│   ├── js/
│   └── icons/
│
├── database/
│   └── vault.db
│
└── backups/
```

---

## Установка

```bash
git clone <repository_url>

cd password_vault

python -m venv venv

venv\Scripts\activate

pip install -r requirements.txt
```

---

## Запуск

```bash
python app.py
```

После запуска приложение:

* Создаст базу данных SQLite
* Запустит локальный веб-сервер
* Автоматически откроет браузер
* Будет доступно по адресу:

```text
http://localhost:8000
```

---

## Первый запуск

При первом запуске необходимо:

1. Создать мастер-пароль
2. Подтвердить мастер-пароль
3. Войти в хранилище
4. Добавить первые записи

⚠️ Важно: мастер-пароль невозможно восстановить. Храните его в надежном месте.

---

# English

## Description

**Password Vault Pro** is a modern local password and secrets manager built with Python and Flask.

The application allows users to securely store:

* Login credentials
* Passwords
* API keys
* Access tokens
* Server credentials
* Secure notes
* Confidential information

All data is stored locally and encrypted before being written to the database.

---

## Features

### Security

* Master password authentication
* AES-256 encryption
* PBKDF2 key derivation
* Master password is never stored
* Automatic vault locking
* Fully offline operation
* No cloud dependency

### Record Management

* Create records
* Edit records
* Delete records
* Archive records
* Favorites
* Color-coded cards
* Categories and tags

### Password Generator

Customizable options:

* Length from 8 to 64 characters
* Special symbols
* Numbers
* Uppercase letters
* Exclude similar characters

### Search & Filtering

* Instant search
* Category filtering
* Tag filtering
* Favorites filtering
* Date filtering

### Backup & Restore

Supported formats:

Export:

* JSON
* CSV

Import:

* JSON
* CSV

Encrypted backups and restore functionality.

### User Interface

* Dark theme
* Glassmorphism design
* Responsive layout
* Smooth animations
* Toast notifications
* Statistics dashboard

---

## Technology Stack

### Backend

* Python 3.13+
* Flask
* SQLAlchemy
* SQLite
* Cryptography

### Frontend

* HTML5
* CSS3
* JavaScript
* Bootstrap 5
* Font Awesome

---

## Installation

```bash
git clone <repository_url>

cd password_vault

python -m venv venv

source venv/bin/activate

pip install -r requirements.txt
```

---

## Run

```bash
python app.py
```

After launch the application will:

* Create the SQLite database
* Start the local web server
* Open the default browser automatically
* Become available at:

```text
http://localhost:8000
```

---

## First Launch

When starting for the first time:

1. Create a master password
2. Confirm the master password
3. Unlock the vault
4. Start adding records

⚠️ Important: The master password cannot be recovered. Store it securely.

---

## License

MIT License

Copyright (c) 2026 Password Vault Pro

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files to deal in the Software without restriction.
