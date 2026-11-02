# Cloud Maker

Решение задания по запуску виртуальных машин на QEMU/KVM через API в Docker.

## Реализованные пункты:

- Базовое задание: Запуск ВМ через virt-install без GUI.
- HTTP API: FastAPI для управления ВМ (создание, удаление, список).
- Cloud-init: Генерация seed.iso для автоматической настройки ВМ (hostname, пользователи).
- Сети и бридж: Используется сеть libvirt default.
- Приложение в контейнере: Docker, управление хостом через сокет /var/run/libvirt/libvirt-sock.
- Восстановление состояния: Сохранение данных в SQLite.
- Реестр образов: API для добавления образов.
- Мониторинг: Prometheus + Grafana.
- Квоты: Проверка лимитов RAM перед созданием ВМ.
- Скрипт проверки: test.sh.
- Скрипт очистки: clean.sh.

## Как запустить

1. Установка зависимостей:
sudo apt install -y qemu-system-x86 libvirt-daemon-system virtinst genisoimage docker.io docker-compose-v2
sudo systemctl enable --now libvirtd docker
sudo usermod -aG libvirt,kvm,docker $USER

После этого нужно перезагрузить компьютер.

2. Перейти в папку с проектом и запустить:
cd ~/cloud-maker/app
sudo docker compose up -d --build

3. Запустить тест:
./test.sh

4. Очистить ресурсы:
./clean.sh

## Скриншоты

1. 01-virsh-empty.png - пустой virsh list
2. 02-cloud-init-login.png - логин в ВМ
3. 03-cloud-init-hostname.png - проверка hostname
4. 04-api-curl.png - curl запрос
5. 05-api-swagger.png - Swagger
6. 06-quota-exceeded.png - ошибка квоты
7. 07-api-create-success.png - создание ВМ
8. 08-virsh-two-vms.png - список ВМ
9. 09-test-script.png - test.sh
10. 10-clean-script.png - clean.sh
11. 11-grafana-dashboard.png - Grafana
12. 12-prometheus-up.png - Prometheus
13. 13-api-delete-success.png - удаление ВМ
