#!/bin/bash
set -e

echo "=== 1. Проверка статуса API ==="
curl -s http://localhost:8000/api/v1/vms

echo -e "\n=== 2. Создание тестовой ВМ через API ==="
curl -s -X POST http://localhost:8000/api/v1/vms \
  -H "Content-Type: application/json" \
  -d '{"name": "test-vm-api", "memory_mb": 128, "vcpus": 1}'

echo -e "\n=== 3. Проверка, что ВМ появилась в гипервизоре ==="
virsh list --all | grep test-vm-api

echo -e "\n=== 4. Удаление тестовой ВМ через API ==="
curl -s -X DELETE http://localhost:8000/api/v1/vms/test-vm-api

echo -e "\n=== Тест успешно пройден! ==="
