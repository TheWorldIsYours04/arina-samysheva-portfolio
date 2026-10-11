# Портфолио Арины Самышевой

Автономный сайт-портфолио графического дизайнера. Используются HTML, CSS, JavaScript, GitHub Pages и Formspree; Adobe Portfolio для работы сайта не требуется.

Страницы: главная, девять дизайн-проектов, контакты.

Публикация через GitHub Actions из ветки `main`. Контактный адрес: arina.samysheva@mail.ru. Форма: https://formspree.io/f/myekpnod.

## Публикация

Откройте `Settings → Pages` и выберите `Build and deployment → Source: GitHub Actions`. После этого изменения ветки `main` автоматически публикуются через `.github/workflows/deploy.yml`.

Изображения проектов включены в репозиторий в виде исходных файлов, упакованных для доставки. GitHub Actions распаковывает их до запуска сайта.

Контактный адрес и Formspree ID настраиваются в `source/settings.json`. Для смены адреса получателя писем также измените его в интерфейсе Formspree (не только на сайте).
