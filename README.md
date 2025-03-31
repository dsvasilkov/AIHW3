# Описание API
Сервис использует JWT-токены для аутентификации пользователей.

 ### POST	/auth/register	- Регистрация пользователя
 ### POST	/auth/token	- Получение JWT-токена
### POST	/links/shorten	Создать короткую ссылку
### GET	/links/{short_code}	Перенаправление по сокращенной ссылке
### DELETE	/links/{short_code}	Удалить ссылку
### PUT	/links/{short_code}	Обновить ссылку
### GET	/links/{short_code}/stats	Получить статистику по ссылке
### GET	/links/search?original_url=	Найти ссылки по оригинальному URL
### GET	/links/expired	Получить список удаленных ссылок
### POST	/set_cleanup_days	Фоновое удаление неиспользуемых ссылок


# Описание БД

### **Таблица `users` (Пользователи)**  

| Поле             | Тип       | Описание                |
|-----------------|----------|-------------------------|
| `id`           | INTEGER  | Уникальный ID          |
| `email`        | STRING   | Email пользователя     |
| `hashed_password` | STRING | Хешированный пароль    |

### **Таблица `links` (Ссылки)**  

| Поле            | Тип       | Описание                   |
|----------------|----------|----------------------------|
| `id`          | INTEGER  | Уникальный ID             |
| `short_code`  | STRING   | Сокращенный код            |
| `original_url` | STRING   | Исходный URL              |
| `created_at`  | DATETIME | Дата создания             |
| `last_used_at` | DATETIME | Последнее использование  |
| `visit_count`  | INTEGER  | Количество переходов     |
| `expires_at`   | DATETIME | Срок действия             |
| `user_id`      | INTEGER  | ID владельца ссылки      |

### **Таблица `expired_links` (Удаленные ссылки)**  

| Поле            | Тип       | Описание                   |
|----------------|----------|----------------------------|
| `id`          | INTEGER  | Уникальный ID             |
| `short_code`  | STRING   | Сокращенный код            |
| `original_url` | STRING   | Исходный URL              |
| `created_at`  | DATETIME | Дата создания             |
| `last_used_at` | DATETIME | Последнее использование  |
| `visit_count`  | INTEGER  | Количество переходов     |
| `expired_at`   | DATETIME | Дата удаления            |
| `user_id`      | INTEGER  | ID владельца ссылки      |
