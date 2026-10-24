# Первый деплой Tribe на FST.KZ (Казахстан)

**Статус:** подготовка. Никакие изменения на VPS не выполнялись автоматически.
Первый production-деплой запускается вручную: Actions → Deploy Tribe → Run workflow (branch master).
Далее включается автоматический деплой по push в master или публикации GitHub Release:
Settings → Secrets and variables → Actions → Variables → New repository variable
`TRIBE_AUTO_DEPLOY=true`. Пока переменная отсутствует или имеет значение `false`,
push/release создают пропущенный запуск, а не деплой.
Не устанавливайте self-hosted runner. CI выполняется на GitHub-hosted ubuntu-latest.

Данные: FST.KZ Premium 100C, публичный IPv4 95.56.251.147, домен tribe.zzzzzzzzzzzzz.cc,
SSH 22. Версия Ubuntu — ранее пользователь сообщил **26.04 LTS**, но в последней анкете осталось
24.04; проверьте с помощью lsb_release -a. Docker поддерживает обе версии.

## 1. DNS в GoDaddy

Создайте/проверьте ТОЛЬКО запись A: имя tribe, значение 95.56.251.147.
Не меняйте записи SQL practice или другие существующие A/CNAME/MX/TXT.
Важно: имя и значение должны быть проверены через публичный DNS:

~~~bash
dig +short A tribe.zzzzzzzzzzzzz.cc
~~~

Пока там нет 95.56.251.147, не пытайтесь выпускать сертификат Let's Encrypt.

## 2. Создайте SSH-ключи на Mac (локально, НЕ на сервере)

Один административный ключ и второй отдельный для GitHub Actions.
Приватные ключи никогда не публикуются и не отправляются в чат.

~~~bash
ssh-keygen -t ed25519 -f ~/.ssh/tribe_admin -C tribe-admin
ssh-keygen -t ed25519 -f ~/.ssh/tribe_deploy -C tribe-github-actions -N ""
~~~

Подключитесь по текущему SSH-логину от провайдера (например root) и установите
административный публичный ключ (замените содержимое команд своим публичным ключом):

~~~bash
cat ~/.ssh/tribe_admin.pub | ssh root@95.56.251.147 'umask 077; mkdir -p ~/.ssh; cat >> ~/.ssh/authorized_keys'
ssh -i ~/.ssh/tribe_admin root@95.56.251.147
~~~

Не отключайте пароль/root login до успешной проверки входа по административному ключу
из НОВОГО терминала.

## 3. Инициализация VPS (SSH по административному ключу)

~~~bash
ssh -i ~/.ssh/tribe_admin root@95.56.251.147
lsb_release -a
free -h
df -h
apt-get update
apt-get upgrade -y
apt-get install -y ca-certificates curl gnupg ufw fail2ban git
~~~

Docker Engine + Compose Plugin: используйте официальный apt-репозиторий Docker
(подходит для Ubuntu 24.04 и 26.04):

~~~bash
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
printf '%s\n' "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" > /etc/apt/sources.list.d/docker.list
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
systemctl enable --now docker
docker compose version
~~~

Создайте пользователя CI. Членство в группе docker даёт практически root-доступ;
этот пользователь предназначен только для деплоя. Не устанавливайте self-hosted runner.

~~~bash
adduser --disabled-password --gecos "" tribe-deploy
usermod -aG docker tribe-deploy
install -d -m 700 -o tribe-deploy -g tribe-deploy /home/tribe-deploy/.ssh
install -d -m 750 -o tribe-deploy -g tribe-deploy /opt/tribe
~~~

Для CI-ключа указан пустой пароль: GitHub-hosted runner должен иметь возможность
использовать его без ручного ввода. Сам ключ хранится только в GitHub Secret.

На Mac отправьте только публичный deploy-ключ:
~~~bash
cat ~/.ssh/tribe_deploy.pub | ssh -i ~/.ssh/tribe_admin root@95.56.251.147 \
  'cat >> /home/tribe-deploy/.ssh/authorized_keys && chown tribe-deploy:tribe-deploy /home/tribe-deploy/.ssh/authorized_keys && chmod 600 /home/tribe-deploy/.ssh/authorized_keys'
ssh -i ~/.ssh/tribe_deploy tribe-deploy@95.56.251.147 'docker version && test -w /opt/tribe'
~~~

Только после проверки обоих ключей ограничьте SSH по паролям и root-входу:
~~~bash
cat > /etc/ssh/sshd_config.d/99-tribe-hardening.conf <<'EOF'
PubkeyAuthentication yes
PasswordAuthentication no
KbdInteractiveAuthentication no
PermitRootLogin prohibit-password
EOF
sshd -t && systemctl reload ssh
~~~
Отдельно проверьте, что вход по ключу root и tribe-deploy сохранился.

Настройте файрвол, не закрывая SSH до проверки:
~~~bash
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw default deny incoming
ufw default allow outgoing
ufw --force enable
ufw status
systemctl enable --now fail2ban
~~~

Не открывайте извне 5432 (PostgreSQL), 6379 (Redis) и 6333 (Qdrant).
Имейте в виду: Docker-published ports обходят часть правил UFW;
production-compose публикует только 80/443 у прокси.

## 4. Переменные окружения и секреты VPS

На Mac клонируйте репозиторий (или скачайте файл deploy/env.production.example)
и передайте шаблон безопасным SSH-каналом:

~~~bash
git clone https://github.com/zzzzzzzzzzzzz/tribe.git
scp -i ~/.ssh/tribe_deploy tribe/deploy/env.production.example \
  tribe-deploy@95.56.251.147:/opt/tribe/.env
~~~

На VPS отредактируйте /opt/tribe/.env:
~~~bash
ssh -i ~/.ssh/tribe_deploy tribe-deploy@95.56.251.147
chmod 600 /opt/tribe/.env
nano /opt/tribe/.env
~~~

Замените все REPLACE_WITH_* на разные случайные значения. Генератор:
~~~bash
python3 -c 'import secrets; print(secrets.token_urlsafe(48))'
~~~

Укажите реальные FIRST_SUPERUSER и ACME_EMAIL.
API-ключ OPENAI_API_KEY нужен лишь при использовании OpenAI; его можно добавить позже.
Ничего из заполненного файла .env не коммитьте. Удалите ненужные переменные
или оставьте пустыми. Не начинайте деплой с фиктивными паролями или email.

## 5. GitHub Secrets

В репозитории zzzzzzzzzzzzz/tribe → Settings → Secrets and variables → Actions
→ New repository secret создайте:

1. VPS_DEPLOY_SSH_KEY: точное содержимое ЛОКАЛЬНОГО приватного ключа
   ~/.ssh/tribe_deploy, с BEGIN/END и переносами строк. В ЧАТ НЕ ПРИСЫЛАТЬ.
2. VPS_SSH_KNOWN_HOSTS: SSH host key сервера. Получите с Mac:
   ssh-keyscan -t ed25519 95.56.251.147
   **Проверьте fingerprint** host key по независимому доверенному источнику
   (панель/консоль VPS) перед добавлением. Не считайте ssh-keyscan подтверждением подлинности.

В репозитории используйте Environment с именем production (при необходимости — с ручным
подтверждением). Репозиторий публичный; первый деплой запускается вручную из master.
Автоматический запуск push/release блокирует `TRIBE_AUTO_DEPLOY`, пока она не установлена
в `true`. Встроенный GITHUB_TOKEN используется для GHCR.

## 6. Запуск вручную

GitHub → Actions → Deploy Tribe → Run workflow → master.
Workflow соберёт backend и frontend через GitHub-hosted runner, загрузит в GHCR,
скопирует файлы Compose и deploy/remote-deploy.sh на VPS, временно авторизуется в GHCR с GITHUB_TOKEN,
поднимет Traefik и основной стек.

Traefik v3.6 использует Let's Encrypt, HTTP challenge на порту 80.
Dashboard наружу не публикуется. Внешние порты только 80 и 443.
Исключены n8n, n8n-worker, Adminer, Flower, self-hosted runner.
Контейнеры PostgreSQL 16, Redis 7.4, Qdrant 1.11.5, backend, celery, frontend.

Локальная разработка использует упрощённый `docker-compose.yml` без Traefik; production всегда использует только файлы из каталога `deploy/`.

**Важно:** первый билд ещё не был выполнен. В частности, старый Python-образ
backend и зависимости могут потребовать корректировок по результатам CI.
Изменения сделаны только в GitHub; нет автоматического доступа к самому VPS.

Проверка после деплоя:
~~~bash
curl -I https://tribe.zzzzzzzzzzzzz.cc
ssh -i ~/.ssh/tribe_deploy tribe-deploy@95.56.251.147 \
  'cd /opt/tribe && docker compose -p tribe-prod --env-file .env -f compose.prod.yml ps && docker stats --no-stream'
~~~

## 7. Данные, backups и ограничения

Все Docker volumes содержат persistent data, но регулярные резервные копии
PostgreSQL, Qdrant и загруженных файлов нужно настроить отдельно.
Не применять docker compose down -v в production.
Не использовать автоматический prune volumes.
База PostgreSQL 16 рассчитана на НОВЫЙ сервер без старого PostgreSQL 12 volume.
Для переноса существующих данных нужна отдельная миграция.
