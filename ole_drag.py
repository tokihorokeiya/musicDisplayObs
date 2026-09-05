"""
Native Windows OLE Drag-and-Drop for URLs into OBS Studio.
Provides standard UniformResourceLocator, UniformResourceLocatorW, text/uri-list,
and fallback text formats via COM IDataObject and IDropSource interfaces.
"""

import sys
import ctypes

IS_WINDOWS = sys.platform == "win32"

if IS_WINDOWS:
    from ctypes import wintypes

    ole32 = ctypes.windll.ole32
    kernel32 = ctypes.windll.kernel32
    user32 = ctypes.windll.user32
    shell32 = ctypes.windll.shell32

    # Clipboard format identifiers
    CF_TEXT = 1
    CF_UNICODETEXT = 13
    CF_URL = user32.RegisterClipboardFormatW("UniformResourceLocator")
    CF_URL_W = user32.RegisterClipboardFormatW("UniformResourceLocatorW")
    CF_URI_LIST = user32.RegisterClipboardFormatW("text/uri-list")

    DVASPECT_CONTENT = 1
    TYMED_HGLOBAL = 1
    DROPEFFECT_NONE = 0
    DROPEFFECT_COPY = 1
    DROPEFFECT_MOVE = 2
    DROPEFFECT_LINK = 4

    S_OK = 0
    DRAGDROP_S_DROP = 0x00040100
    DRAGDROP_S_CANCEL = 0x00040101
    DRAGDROP_S_USEDEFAULTCURSORS = 0x00040102
    E_NOTIMPL = -2147467263       # 0x80004001
    E_FAIL = -2147467259          # 0x80004005
    E_NOINTERFACE = -2147467262   # 0x80004002
    DV_E_FORMATETC = -2147221404  # 0x80040064
    MK_LBUTTON = 0x0001

    class GUID(ctypes.Structure):
        _fields_ = [
            ("Data1", wintypes.DWORD),
            ("Data2", wintypes.WORD),
            ("Data3", wintypes.WORD),
            ("Data4", ctypes.c_ubyte * 8),
        ]

    IID_IUnknown = GUID(0x00000000, 0x0000, 0x0000, (ctypes.c_ubyte * 8)(0xC0, 0, 0, 0, 0, 0, 0, 0x46))
    IID_IDataObject = GUID(0x0000010E, 0x0000, 0x0000, (ctypes.c_ubyte * 8)(0xC0, 0, 0, 0, 0, 0, 0, 0x46))
    IID_IDropSource = GUID(0x00000121, 0x0000, 0x0000, (ctypes.c_ubyte * 8)(0xC0, 0, 0, 0, 0, 0, 0, 0x46))

    IID_IUnknown_BYTES = bytes(IID_IUnknown)
    IID_IDataObject_BYTES = bytes(IID_IDataObject)
    IID_IDropSource_BYTES = bytes(IID_IDropSource)

    class FORMATETC(ctypes.Structure):
        _fields_ = [
            ("cfFormat", wintypes.UINT),
            ("ptd", ctypes.c_void_p),
            ("dwAspect", wintypes.DWORD),
            ("lindex", wintypes.LONG),
            ("tymed", wintypes.DWORD),
        ]

    class STGMEDIUM(ctypes.Structure):
        _fields_ = [
            ("tymed", wintypes.DWORD),
            ("hGlobal", wintypes.HANDLE),
            ("pUnkForRelease", ctypes.c_void_p),
        ]

    QueryInterfaceProto = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p)
    AddRefReleaseProto = ctypes.WINFUNCTYPE(ctypes.c_ulong, ctypes.c_void_p)

    QueryContinueDragProto = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p, wintypes.BOOL, wintypes.DWORD)
    GiveFeedbackProto = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p, wintypes.DWORD)

    GetDataProto = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p, ctypes.POINTER(FORMATETC), ctypes.POINTER(STGMEDIUM))
    GetDataHereProto = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p, ctypes.POINTER(FORMATETC), ctypes.POINTER(STGMEDIUM))
    QueryGetDataProto = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p, ctypes.POINTER(FORMATETC))
    GetCanonicalFormatEtcProto = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p, ctypes.POINTER(FORMATETC), ctypes.POINTER(FORMATETC))
    SetDataProto = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p, ctypes.POINTER(FORMATETC), ctypes.POINTER(STGMEDIUM), wintypes.BOOL)
    EnumFormatEtcProto = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p, wintypes.DWORD, ctypes.c_void_p)
    DAdviseProto = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p, ctypes.POINTER(FORMATETC), wintypes.DWORD, ctypes.c_void_p, ctypes.POINTER(wintypes.DWORD))
    DUnadviseProto = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p, wintypes.DWORD)
    EnumDAdviseProto = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p, ctypes.c_void_p)

    class DropSourceVtbl(ctypes.Structure):
        _fields_ = [
            ("QueryInterface", QueryInterfaceProto),
            ("AddRef", AddRefReleaseProto),
            ("Release", AddRefReleaseProto),
            ("QueryContinueDrag", QueryContinueDragProto),
            ("GiveFeedback", GiveFeedbackProto),
        ]

    class DataObjectVtbl(ctypes.Structure):
        _fields_ = [
            ("QueryInterface", QueryInterfaceProto),
            ("AddRef", AddRefReleaseProto),
            ("Release", AddRefReleaseProto),
            ("GetData", GetDataProto),
            ("GetDataHere", GetDataHereProto),
            ("QueryGetData", QueryGetDataProto),
            ("GetCanonicalFormatEtc", GetCanonicalFormatEtcProto),
            ("SetData", SetDataProto),
            ("EnumFormatEtc", EnumFormatEtcProto),
            ("DAdvise", DAdviseProto),
            ("DUnadvise", DUnadviseProto),
            ("EnumDAdvise", EnumDAdviseProto),
        ]

    GMEM_MOVEABLE = 0x0002
    GMEM_ZEROINIT = 0x0040

    kernel32.GlobalAlloc.restype = ctypes.c_void_p
    kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]

    shell32.SHCreateStdEnumFmtEtc.restype = ctypes.c_long
    shell32.SHCreateStdEnumFmtEtc.argtypes = [wintypes.UINT, ctypes.c_void_p, ctypes.c_void_p]

    ole32.OleInitialize.restype = ctypes.c_long
    ole32.OleInitialize.argtypes = [ctypes.c_void_p]

    ole32.DoDragDrop.restype = ctypes.c_long
    ole32.DoDragDrop.argtypes = [ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]

    def alloc_global_bytes(raw_bytes):
        h = kernel32.GlobalAlloc(GMEM_MOVEABLE | GMEM_ZEROINIT, len(raw_bytes))
        ptr = kernel32.GlobalLock(h)
        ctypes.memmove(ptr, raw_bytes, len(raw_bytes))
        kernel32.GlobalUnlock(h)
        return h

    class NativeDropSource:
        def __init__(self):
            self.ref_count = 1
            self._vtbl = DropSourceVtbl(
                QueryInterface=QueryInterfaceProto(self.QueryInterface),
                AddRef=AddRefReleaseProto(self.AddRef),
                Release=AddRefReleaseProto(self.Release),
                QueryContinueDrag=QueryContinueDragProto(self.QueryContinueDrag),
                GiveFeedback=GiveFeedbackProto(self.GiveFeedback)
            )
            self._vtbl_ptr = ctypes.pointer(self._vtbl)

        @property
        def interface_ptr(self):
            return ctypes.cast(ctypes.pointer(self._vtbl_ptr), ctypes.c_void_p)

        def QueryInterface(self, this, riid, ppv):
            if not ppv:
                return E_FAIL
            guid_bytes = ctypes.string_at(riid, 16)
            if guid_bytes in (IID_IUnknown_BYTES, IID_IDropSource_BYTES):
                ctypes.cast(ppv, ctypes.POINTER(ctypes.c_void_p))[0] = this
                self.AddRef(this)
                return S_OK
            ctypes.cast(ppv, ctypes.POINTER(ctypes.c_void_p))[0] = None
            return E_NOINTERFACE

        def AddRef(self, this):
            self.ref_count += 1
            return self.ref_count

        def Release(self, this):
            self.ref_count -= 1
            return self.ref_count

        def QueryContinueDrag(self, this, fEscapePressed, grfKeyState):
            if fEscapePressed:
                return DRAGDROP_S_CANCEL
            # Release when left mouse button is released
            if not (grfKeyState & MK_LBUTTON):
                return DRAGDROP_S_DROP
            return S_OK

        def GiveFeedback(self, this, dwEffect):
            return DRAGDROP_S_USEDEFAULTCURSORS

    class NativeUrlDataObject:
        def __init__(self, url):
            self.url = str(url)
            self.ref_count = 1

            # Provide all standard URL and text clipboard formats
            self.formats = [
                FORMATETC(CF_URL, None, DVASPECT_CONTENT, -1, TYMED_HGLOBAL),
                FORMATETC(CF_URL_W, None, DVASPECT_CONTENT, -1, TYMED_HGLOBAL),
                FORMATETC(CF_URI_LIST, None, DVASPECT_CONTENT, -1, TYMED_HGLOBAL),
                FORMATETC(CF_UNICODETEXT, None, DVASPECT_CONTENT, -1, TYMED_HGLOBAL),
                FORMATETC(CF_TEXT, None, DVASPECT_CONTENT, -1, TYMED_HGLOBAL),
            ]
            self.format_array = (FORMATETC * len(self.formats))(*self.formats)

            self._vtbl = DataObjectVtbl(
                QueryInterface=QueryInterfaceProto(self.QueryInterface),
                AddRef=AddRefReleaseProto(self.AddRef),
                Release=AddRefReleaseProto(self.Release),
                GetData=GetDataProto(self.GetData),
                GetDataHere=GetDataHereProto(self.GetDataHere),
                QueryGetData=QueryGetDataProto(self.QueryGetData),
                GetCanonicalFormatEtc=GetCanonicalFormatEtcProto(self.GetCanonicalFormatEtc),
                SetData=SetDataProto(self.SetData),
                EnumFormatEtc=EnumFormatEtcProto(self.EnumFormatEtc),
                DAdvise=DAdviseProto(self.DAdvise),
                DUnadvise=DUnadviseProto(self.DUnadvise),
                EnumDAdvise=EnumDAdviseProto(self.EnumDAdvise)
            )
            self._vtbl_ptr = ctypes.pointer(self._vtbl)

        @property
        def interface_ptr(self):
            return ctypes.cast(ctypes.pointer(self._vtbl_ptr), ctypes.c_void_p)

        def QueryInterface(self, this, riid, ppv):
            try:
                if not ppv:
                    return E_FAIL
                guid_bytes = ctypes.string_at(riid, 16)
                if guid_bytes in (IID_IUnknown_BYTES, IID_IDataObject_BYTES):
                    ctypes.cast(ppv, ctypes.POINTER(ctypes.c_void_p))[0] = this
                    self.AddRef(this)
                    return S_OK
                ctypes.cast(ppv, ctypes.POINTER(ctypes.c_void_p))[0] = None
                return E_NOINTERFACE
            except Exception:
                return E_FAIL

        def AddRef(self, this):
            self.ref_count += 1
            return self.ref_count

        def Release(self, this):
            self.ref_count -= 1
            return self.ref_count

        def QueryGetData(self, this, pFormatEtc):
            try:
                if not pFormatEtc:
                    return DV_E_FORMATETC
                cf = pFormatEtc.contents.cfFormat
                if cf in (CF_URL, CF_URL_W, CF_URI_LIST, CF_UNICODETEXT, CF_TEXT):
                    return S_OK
                return DV_E_FORMATETC
            except Exception:
                return DV_E_FORMATETC

        def GetData(self, this, pFormatEtc, pStgMedium):
            try:
                if not pFormatEtc or not pStgMedium:
                    return E_FAIL
                cf = pFormatEtc.contents.cfFormat

                if cf == CF_URL:
                    raw = self.url.encode("ascii", errors="ignore") + b"\x00"
                elif cf == CF_URL_W:
                    raw = (self.url + "\x00").encode("utf-16le")
                elif cf == CF_URI_LIST:
                    raw = (self.url + "\r\n\x00").encode("utf-8")
                elif cf == CF_UNICODETEXT:
                    raw = (self.url + "\x00").encode("utf-16le")
                elif cf == CF_TEXT:
                    raw = self.url.encode("ascii", errors="ignore") + b"\x00"
                else:
                    return DV_E_FORMATETC

                pStgMedium.contents.tymed = TYMED_HGLOBAL
                pStgMedium.contents.hGlobal = alloc_global_bytes(raw)
                pStgMedium.contents.pUnkForRelease = None
                return S_OK
            except Exception:
                return E_FAIL

        def GetDataHere(self, this, pFormatEtc, pStgMedium):
            return E_NOTIMPL

        def GetCanonicalFormatEtc(self, this, pFormatEtcIn, pFormatEtcOut):
            return E_NOTIMPL

        def SetData(self, this, pFormatEtc, pStgMedium, fRelease):
            return E_NOTIMPL

        def EnumFormatEtc(self, this, dwDirection, ppEnumFormatEtc):
            try:
                if dwDirection == 1 and ppEnumFormatEtc:  # DATADIR_GET
                    return shell32.SHCreateStdEnumFmtEtc(
                        ctypes.c_uint(len(self.formats)),
                        ctypes.cast(ctypes.byref(self.format_array), ctypes.c_void_p),
                        ctypes.c_void_p(ppEnumFormatEtc)
                    )
                return E_NOTIMPL
            except Exception:
                return E_NOTIMPL

        def DAdvise(self, this, pFormatEtc, advf, pAdvSink, pdwConnection):
            return E_NOTIMPL

        def DUnadvise(self, this, dwConnection):
            return E_NOTIMPL

        def EnumDAdvise(self, this, ppEnumAdvise):
            return E_NOTIMPL

    def perform_ole_url_drag(url):
        """Initiates a native Windows OLE drag-and-drop operation for a URL."""
        try:
            ole32.OleInitialize(None)
            data_obj = NativeUrlDataObject(url)
            drop_src = NativeDropSource()
            dw_effect = wintypes.DWORD(0)

            res = ole32.DoDragDrop(
                data_obj.interface_ptr,
                drop_src.interface_ptr,
                DROPEFFECT_COPY | DROPEFFECT_LINK,
                ctypes.byref(dw_effect)
            )
            # DRAGDROP_S_DROP (0x00040100) or S_OK (0) indicates successful drop
            is_success = (res in (0, 0x00040100)) and (dw_effect.value != DROPEFFECT_NONE)
            return is_success, res
        except Exception as e:
            print("[OLE Drag Error]", e)
            return False, -1

else:
    def perform_ole_url_drag(url):
        return False, -1


def setup_native_drag_and_drop(widget, get_url_func, on_drag_success_callback=None, on_click_callback=None):
    """
    Binds native Windows OLE drag-and-drop to any Tkinter / CustomTkinter widget.
    - Click (< 6px movement): triggers on_click_callback
    - Drag (>= 6px movement): starts native OLE DoDragDrop with URL into OBS Studio
    """
    state = {
        "start_x": 0,
        "start_y": 0,
        "is_dragging": False,
    }

    def _resolve_url():
        try:
            return get_url_func() if callable(get_url_func) else str(get_url_func)
        except Exception:
            return ""

    def on_press(event):
        state["start_x"] = event.x_root
        state["start_y"] = event.y_root
        state["is_dragging"] = False

    def on_motion(event):
        if not state["is_dragging"]:
            dx = abs(event.x_root - state["start_x"])
            dy = abs(event.y_root - state["start_y"])
            if dx > 6 or dy > 6:
                state["is_dragging"] = True
                url = _resolve_url()
                if not url:
                    return
                success, code = perform_ole_url_drag(url)
                if success and on_drag_success_callback:
                    try:
                        on_drag_success_callback()
                    except Exception:
                        pass

    def on_release(event):
        if not state["is_dragging"]:
            url = _resolve_url()
            if on_click_callback:
                try:
                    on_click_callback(url)
                except Exception:
                    pass

    # Support CustomTkinter wrapper widgets by also binding inner tk components
    targets = [widget]
    for attr in ("_entry", "_label", "_canvas", "_text"):
        if hasattr(widget, attr):
            inner = getattr(widget, attr)
            if inner and hasattr(inner, "bind"):
                targets.append(inner)

    for w in targets:
        try:
            w.bind("<ButtonPress-1>", on_press, add="+")
            w.bind("<B1-Motion>", on_motion, add="+")
            w.bind("<ButtonRelease-1>", on_release, add="+")
        except Exception:
            pass
