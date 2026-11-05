#!/bin/bash
set -e

echo "=== 0. Подготовка seed.iso (cloud-init) ==="
cat > /tmp/user-data << 'YAML'
#cloud-config
hostname: cloud-node-01
users:
  - name: clouduser
    sudo: ALL=(ALL) NOPASSWD:ALL
    shell: /bin/bash
    lock_passwd: false
    passwd: "$6$rounds=4096$saltsalt$wT8.1S/1uT.w2uT.w2uT.w2uT.w2uT.w2uT.w2uT.w2uT.w2uT"
chpasswd:
  list: |
    root:12345
  expire: False
ssh_pwauth: True
YAML

cat > /tmp/meta-data << 'YAML'
instance-id: i-cloud-01
local-hostname: cloud-node-01
YAML

genisoimage -output /tmp/seed.iso -volid cidata -joliet -rock /tmp/user-data /tmp/meta-data > /dev/null 2>&1
sudo mv /tmp/seed.iso /var/lib/libvirt/images/seed.iso
sudo chmod 644 /var/lib/libvirt/images/seed.iso

echo "=== 1. Проверка статуса API ==="
curl -s http://localhost:8000/api/v1/vms

echo -e "\n=== 2. Создание тестовой ВМ через API ==="
curl -s -X POST http://localhost:8000/api/v1/vms \
  -H "Content-Type: application/json" \
  -d '{"name": "test-vm-api", "memory_mb": 512, "vcpus": 1}'

echo -e "\n=== 3. Проверка, что ВМ появилась в гипервизоре ==="
sleep 2
virsh list --all | grep test-vm-api

echo -e "\n=== 4. Удаление тестовой ВМ через API ==="
curl -s -X DELETE http://localhost:8000/api/v1/vms/test-vm-api

echo -e "\n=== Тест успешно пройден! ==="
