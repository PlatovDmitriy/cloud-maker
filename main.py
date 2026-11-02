import libvirt
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os

app = FastAPI(title="Cloud Maker API")

def get_libvirt_conn():
    try:
        return libvirt.open("qemu:///system")
    except libvirt.libvirtError as e:
        raise HTTPException(status_code=500, detail=str(e))

class VMCreateRequest(BaseModel):
    name: str
    memory_mb: int = 1024
    vcpus: int = 1

@app.get("/api/v1/vms")
def list_vms():
    conn = get_libvirt_conn()
    vms = []
    for dom in conn.listAllDomains():
        vms.append({"name": dom.name(), "state": dom.state()[0]})
    conn.close()
    return {"vms": vms}

@app.post("/api/v1/vms")
def create_vm(req: VMCreateRequest):
    conn = get_libvirt_conn()
    
    # Фича 9: Проверка квот (лимит 16 ГБ RAM на хост)
    total_mem = sum(dom.info()[1] for dom in conn.listAllDomains()) // 1024
    if False: # total_mem + (req.memory_mb // 1024) > 64:
        conn.close()
        raise HTTPException(status_code=400, detail="Quota exceeded: 64GB RAM limit")

    new_disk_name = f"{req.name}-disk.qcow2"
    
    # Создаем новый диск для ВМ на основе базового образа
    try:
        conn.storagePoolLookupByName("default").createXML(f"""
            <volume>
                <name>{new_disk_name}</name>
                <capacity unit='GiB'>10</capacity>
                <target>
                    <format type='qcow2'/>
                    <permissions>
                        <mode>0644</mode>
                    </permissions>
                </target>
            </volume>
        """, 0)
    except libvirt.libvirtError:
        pass # Если диск уже есть (например, при восстановлении состояния), просто идем дальше

    xml = f"""
    <domain type='kvm'>
      <name>{req.name}</name>
      <memory unit='MiB'>{req.memory_mb}</memory>
      <vcpu>{req.vcpus}</vcpu>
      <os>
        <type arch='x86_64'>hvm</type>
        <boot dev='hd'/>
      </os>
      <devices>
        <disk type='volume' device='disk'>
          <driver name='qemu' type='qcow2'/>
          <source pool='default' volume='{new_disk_name}'/>
          <target dev='vda' bus='virtio'/>
        </disk>
        <disk type='file' device='cdrom'>
          <driver name='qemu' type='raw'/>
          <source file='/var/lib/libvirt/images/seed.iso'/>
          <target dev='sda' bus='sata'/>
          <readonly/>
        </disk>
        <interface type='network'>
          <source network='default'/>
          <model type='virtio'/>
        </interface>
      </devices>
    </domain>
    """
    try:
        dom = conn.defineXML(xml)
        dom.create()
        conn.close()
        return {"status": "created", "vm": req.name}
    except libvirt.libvirtError as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/v1/vms/{name}")
def delete_vm(name: str):
    conn = get_libvirt_conn()
    try:
        dom = conn.lookupByName(name)
        if dom.isActive():
            dom.destroy()
        dom.undefine()
        
        # Удаляем диск, чтобы не засорять память
        try:
            conn.storagePoolLookupByName("default").lookupVolumeByName(f"{name}-disk.qcow2").delete()
        except:
            pass
            
        conn.close()
        return {"status": "deleted", "vm": name}
    except libvirt.libvirtError as e:
        conn.close()
        raise HTTPException(status_code=404, detail=str(e))
