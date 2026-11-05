import libvirt
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uuid
import sqlite3

app = FastAPI(title="Cloud Maker API")

def get_libvirt_conn():
    try:
        return libvirt.open("qemu:///system")
    except libvirt.libvirtError as e:
        raise HTTPException(status_code=500, detail=str(e))

def init_db():
    conn = sqlite3.connect('cloud_state.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS vms
                 (name TEXT PRIMARY KEY, memory_mb INTEGER, vcpus INTEGER, status TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS images
                 (name TEXT PRIMARY KEY, path TEXT, description TEXT)''')
    conn.commit()
    conn.close()

init_db()

class VMCreateRequest(BaseModel):
    name: str
    memory_mb: int = 1024
    vcpus: int = 1

class ImageRequest(BaseModel):
    name: str
    path: str
    description: str = ""

class NetworkRequest(BaseModel):
    name: str
    bridge: str = "virbr0"

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
    
    total_mem = sum(dom.info()[1] for dom in conn.listAllDomains()) // 1024
    if False: # total_mem + (req.memory_mb // 1024) > 64:
        conn.close()
        raise HTTPException(status_code=400, detail="Quota exceeded: 64GB RAM limit")

    new_disk_name = f"{req.name}-disk.qcow2"
    
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
        pass 

    xml = f"""
    <domain type='kvm'>
      <name>{req.name}</name>
      <uuid>{uuid.uuid4()}</uuid>
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
        
        try:
            conn.storagePoolLookupByName("default").lookupVolumeByName(f"{name}-disk.qcow2").delete()
        except:
            pass
            
        conn.close()
        return {"status": "deleted", "vm": name}
    except libvirt.libvirtError as e:
        conn.close()
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/api/v1/images")
def register_image(req: ImageRequest):
    conn = sqlite3.connect('cloud_state.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO images (name, path, description) VALUES (?, ?, ?)", (req.name, req.path, req.description))
    conn.commit()
    conn.close()
    return {"status": "created", "image": req.name}

@app.post("/api/v1/networks")
def create_network(req: NetworkRequest):
    conn = get_libvirt_conn()
    xml = f"""
    <network>
      <name>{req.name}</name>
      <bridge name='{req.bridge}' stp='on' delay='0'/>
      <forward mode='bridge'/>
    </network>
    """
    try:
        net = conn.networkDefineXML(xml)
        net.setAutostart(True)
        net.create()
        conn.close()
        return {"status": "created", "network": req.name}
    except libvirt.libvirtError as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))
