#!/bin/bash
echo "=== Очистка ресурсов Cloud Maker ==="

# Удаляем все ВМ, созданные через API (с префиксом test-)
for vm in $(virsh list --all --name | grep "test-"); do
    echo "Удаляем ВМ: $vm"
    virsh destroy $vm 2>/dev/null || true
    virsh undefine $vm --remove-all-storage 2>/dev/null || true
done

# Удаляем диски, если они остались
sudo virsh vol-delete --pool default test-vm-api-disk.qcow2 2>/dev/null || true

# Удаляем временные файлы
rm -f seed.iso user-data meta-data cloud_state.db

echo "=== Очистка завершена! ==="
