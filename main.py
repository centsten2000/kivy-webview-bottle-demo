# -*- coding: utf-8 -*-
from kivy.app import App
from kivy.lang import Builder
from kivy.utils import platform
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.uix.screenmanager import ScreenManager, Screen
#from generic import DynamicScreen
from kivy.clock import Clock, mainthread
from jnius import autoclass, cast
from android.runnable import run_on_ui_thread
from threading import Thread
import json
import sys
import os
from bottle import run as bottle_run
from bottle import route, request
from bottle import template, static_file
from bottle import HTTPError

# android 类
WebView = autoclass('android.webkit.WebView')
WebViewClient = autoclass('android.webkit.WebViewClient')
activity = autoclass('org.kivy.android.PythonActivity').mActivity

viewroot = None
# bottle相关
webport = 49092
bottle_template_settings = {'syntax': '<% %> % {| |}'}   # 用于解决bottle的{{}}与vue的冲突问题


# bottle静态文件
@route('/static/<filename:path>')
def server_static(filename):
    if 'gizp' in request.headers.get('Accept-Encoding'):
        out = static_file(filename + '.gz', root='%s/static' % os.getcwd())
        if not isinstance(out, HTTPError):
            return out
    return static_file(filename, root='%s/static' % os.getcwd())


@route('/index')
def launcher():
    return template('index', template_settings=bottle_template_settings)


#kivy界面
class WebviewLauncher(Screen):
    def __init__(self, **kwargs):
        global viewroot
        viewroot = self
        super(WebviewLauncher, self).__init__(**kwargs)
        self.webview = None
        self.view_cached = None
        Clock.schedule_once(self.create_webview, 0)

    
    @run_on_ui_thread
    def create_webview(self, *args):
        if not self.view_cached:
            self.view_cached = activity.currentFocus
        self.webview = WebView(activity)
        self.webview.getSettings().setJavaScriptEnabled(True)
        wvc = WebViewClient()
        self.webview.setWebViewClient(wvc)
        ViewGroup = autoclass('android.view.ViewGroup')
        LayoutParams = autoclass('android.view.ViewGroup$LayoutParams')
        params = LayoutParams(LayoutParams.MATCH_PARENT, LayoutParams.MATCH_PARENT)
        activity.addContentView(self.webview, params)
        self.webview.loadUrl('http://127.0.0.1:%s/index' % webport)


    @run_on_ui_thread
    def detach_webview(self, *args):
        if self.webview:
            self.webview.clearHistory()
            self.webview.clearCache(True)
            self.webview.loadUrl('about:blank')
            self.webview.freeMemory()
            activity.setContentView(self.view_cached)
        Clock.schedule_once(self.quit_screen, -1)


    @mainthread
    def quit_screen(self, *args):
        # 根据https://stackoverflow.com/questions/38454505/how-to-deattach-webview-once-attached说，如果不用这个mainthread，项目就会卡住
        app = App.get_running_app()
        app.root.current = 'app'


        

class LauncherApp(App):
    def build(self):
        global viewroot
        sm = ScreenManager()
        sm.add_widget(WebviewLauncher(name='index'))
        return sm

    def on_pause(self):
        return True


if __name__ == "__main__":
    serviceThread = Thread(target=bottle_run, 
                           kwargs={'host': '127.0.0.1',
                                   'port': webport,
                                   'debug': False})
    serviceThread.start()
    LauncherApp().run()
