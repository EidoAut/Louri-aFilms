"""Inspect public player errors and codec support without extracting media URLs."""
import json
import sys
from urllib.parse import urlsplit
from PySide6.QtCore import QTimer, QUrl
from PySide6.QtWidgets import QApplication
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile

app = QApplication(sys.argv)
profile = QWebEngineProfile(app)
page = QWebEnginePage(profile, app)
view = QWebEngineView()
view.setPage(page)
view.resize(1000, 650)
page.newWindowRequested.connect(lambda request: print("POPUP", urlsplit(request.requestedUrl().toString()).hostname, urlsplit(request.requestedUrl().toString()).path, request.isUserInitiated(), flush=True))
page.loadFinished.connect(lambda ok: print("LOAD", ok, flush=True))
page.setUrl(QUrl(sys.argv[1] if len(sys.argv) > 1 else "about:blank"))
def finish(value):
    print("DIAGNOSTIC", value, flush=True)
    page.setUrl(QUrl("about:blank"))
    QTimer.singleShot(100, app.quit)
def inspect():
    page.runJavaScript('''JSON.stringify({h264:document.createElement("video").canPlayType('video/mp4; codecs="avc1.42E01E"'),aac:document.createElement("audio").canPlayType('audio/mp4; codecs="mp4a.40.2"'),vp9:document.createElement("video").canPlayType('video/webm; codecs="vp9"'),text:document.body ? document.body.innerText.slice(0,2500) : "",videos:Array.from(document.querySelectorAll("video")).map(v=>({readyState:v.readyState,error:v.error ? {code:v.error.code,message:v.error.message}:null}))})''', finish)
QTimer.singleShot(18000, inspect)
QTimer.singleShot(25000, app.quit)
app.exec()
view.close()
page.deleteLater()
profile.deleteLater()
app.processEvents()
