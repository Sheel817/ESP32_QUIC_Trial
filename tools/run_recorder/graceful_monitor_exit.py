"""Send only 'exit' to the verified existing monitor's inherited stdin pipe.

No serial access, process termination, reset signal or historical file edits.
"""
import ctypes as c
from ctypes import wintypes as w
import json,time

def send_exit(parent_pid,child_pid):
    k=c.WinDLL('kernel32',use_last_error=True);nt=c.WinDLL('ntdll')
    k.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD];k.OpenProcess.restype=w.HANDLE
    k.GetCurrentProcess.restype=w.HANDLE
    k.CloseHandle.argtypes=[w.HANDLE]
    k.DuplicateHandle.argtypes=[w.HANDLE,w.HANDLE,w.HANDLE,c.POINTER(w.HANDLE),w.DWORD,w.BOOL,w.DWORD]
    k.ReadProcessMemory.argtypes=[w.HANDLE,c.c_void_p,c.c_void_p,c.c_size_t,c.POINTER(c.c_size_t)]
    k.GetFileType.argtypes=[w.HANDLE];k.GetFileType.restype=w.DWORD
    k.GetNamedPipeInfo.argtypes=[w.HANDLE,c.POINTER(w.DWORD),c.POINTER(w.DWORD),c.POINTER(w.DWORD),c.POINTER(w.DWORD)]
    k.GetNamedPipeServerProcessId.argtypes=[w.HANDLE,c.POINTER(w.ULONG)]
    k.WriteFile.argtypes=[w.HANDLE,c.c_void_p,w.DWORD,c.POINTER(w.DWORD),c.c_void_p]
    nt.NtQueryInformationProcess.argtypes=[w.HANDLE,w.ULONG,c.c_void_p,w.ULONG,c.POINTER(w.ULONG)]
    nt.NtQuerySystemInformation.argtypes=[w.ULONG,c.c_void_p,w.ULONG,c.POINTER(w.ULONG)]
    nt.NtQueryObject.argtypes=[w.HANDLE,w.ULONG,c.c_void_p,w.ULONG,c.POINTER(w.ULONG)]
    class Basic(c.Structure):
        _fields_=[('reserved',c.c_void_p),('peb',c.c_void_p),('reserved2',c.c_void_p*2),('pid',c.c_size_t),('reserved3',c.c_void_p)]
    class Entry(c.Structure):
        _fields_=[('obj',c.c_void_p),('pid',c.c_size_t),('handle',c.c_size_t),('access',w.ULONG),('creator',w.USHORT),('type',w.USHORT),('attrs',w.ULONG),('reserved',w.ULONG)]
    class Unicode(c.Structure):
        _fields_=[('length',w.USHORT),('maximum',w.USHORT),('buffer',c.c_void_p)]
    current=k.GetCurrentProcess();parent=k.OpenProcess(0x40,False,parent_pid);child=k.OpenProcess(0x410|0x40,False,child_pid)
    if not parent or not child:raise c.WinError(c.get_last_error())
    handles=[]
    try:
        def pointer_at(address):
            value=c.c_void_p();read=c.c_size_t()
            if not k.ReadProcessMemory(child,address,c.byref(value),c.sizeof(value),c.byref(read)):raise c.WinError(c.get_last_error())
            return value.value
        def duplicate(process,handle):
            value=w.HANDLE()
            if not k.DuplicateHandle(process,w.HANDLE(handle),current,c.byref(value),0,False,2):raise c.WinError(c.get_last_error())
            handles.append(value);return value
        def name(handle):
            buf=c.create_string_buffer(2048);length=w.ULONG()
            if nt.NtQueryObject(handle,1,buf,len(buf),c.byref(length))!=0:return None
            s=Unicode.from_buffer(buf)
            return c.wstring_at(s.buffer,s.length//2) if s.buffer else ''
        info=Basic();length=w.ULONG()
        if nt.NtQueryInformationProcess(child,0,c.byref(info),c.sizeof(info),c.byref(length))!=0:raise RuntimeError('Cannot inspect target monitor stdin')
        params=pointer_at(info.peb+0x20);stdin=pointer_at(params+0x20)
        reference=duplicate(child,stdin)
        assert k.GetFileType(reference)==3,'Monitor stdin is not a pipe'
        # Querying pipe object names can block in Windows. Inspect only bounded
        # handle metadata; require one and only one parent-owned write pipe.
        size=1024*1024
        for _ in range(8):
            buf=c.create_string_buffer(size);needed=w.ULONG()
            status=nt.NtQuerySystemInformation(64,buf,size,c.byref(needed))
            if status==0:break
            size=max(size*2,needed.value+4096)
        else:raise RuntimeError('Cannot enumerate parent pipe handles')
        count=c.c_size_t.from_buffer(buf).value;matches=[];candidates=[]
        for n in range(count):
            entry=Entry.from_buffer(buf,16+n*c.sizeof(Entry))
            if entry.pid!=parent_pid or not entry.access&2:continue
            try:
                handle=duplicate(parent,entry.handle)
                if k.GetFileType(handle)==3:
                    flags=w.DWORD();server=w.ULONG()
                    info_ok=k.GetNamedPipeInfo(handle,c.byref(flags),None,None,None)
                    pid_ok=k.GetNamedPipeServerProcessId(handle,c.byref(server))
                    candidates.append(dict(handle=entry.handle,access=entry.access,flags=flags.value,server_pid=server.value,info_ok=bool(info_ok),pid_ok=bool(pid_ok)))
                    if info_ok and pid_ok and not flags.value&1 and server.value==parent_pid:matches.append((entry.handle,handle))
            except OSError:continue
        assert len(matches)==1,f'Expected one collector-created client-end write pipe; found {len(matches)}; metadata={candidates}'
        data=c.create_string_buffer(b'exit\n');written=w.DWORD()
        if not k.WriteFile(matches[0][1],data,5,c.byref(written),None):raise c.WinError(c.get_last_error())
        assert written.value==5
        return dict(parent_pid=parent_pid,monitor_pid=child_pid,parent_pipe_handle=matches[0][0],command='exit',bytes_written=written.value,method='Require exactly one write-capable pipe in verified old collector parent; verify child stdin is a pipe; SDK monitor exit command; no monitor/process kill')
    finally:
        for handle in handles:k.CloseHandle(handle)
        k.CloseHandle(parent);k.CloseHandle(child)
