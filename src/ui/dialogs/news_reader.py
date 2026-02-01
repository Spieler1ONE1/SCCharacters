from PySide6.QtCore import Qt, QUrl, QRunnable, QThreadPool, Signal,  QObject, Slot, QPropertyAnimation, QEasingCurve, QPoint, QRect
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QWidget, QProgressBar, QFrame, QGraphicsOpacityEffect, QSizeGrip)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineScript, QWebEngineUrlRequestInterceptor, QWebEngineSettings

class WebInterceptor(QWebEngineUrlRequestInterceptor):
    def interceptRequest(self, info):
        qurl = info.requestUrl()
        scheme = qurl.scheme()
        url = qurl.toString().lower()
        
        # Don't block data URIs (used by setHtml) or local resources
        if scheme == "data" or scheme == "qrc":
            return

        # Block heavy tracker/cookie scripts at the network level
        block_list = [
            # "onetrust", 
            # "cookielaw",
            # "cookiebot",
            # "termly",
            # "quantcast"
        ]
        if any(x in url for x in block_list):
            info.block(True)

class PageTranslationWorker(QRunnable):
    def __init__(self, html, lang_code, original_url):
        super().__init__()
        self.signals = TranslationSignals()
        self.html = html
        self.lang_code = lang_code
        self.url = original_url

    @Slot()
    def run(self):
        try:
            from bs4 import BeautifulSoup
            
            # Use the HTML provided by the browser
            soup = BeautifulSoup(self.html, 'html.parser')
            
            # 0. STRIP COOKIE BANNERS (Pre-emptive strike for the translated view)
            # Remove RSI/OneTrust specific elements so they aren't even in the HTML we render
            ignore_selectors = [
                '#onetrust-banner-sdk', 
                '.onetrust-pc-dark-filter', 
                '#onetrust-consent-sdk',
                '.cc-banner',
                '#cookie-law-info-bar'
            ]
            for sel in ignore_selectors:
                for tag in soup.select(sel):
                    tag.decompose()

            # 1. Base URL for assets
            if not soup.find('base'):
                new_base = soup.new_tag('base', href=self.url)
                if soup.head: 
                    soup.head.insert(0, new_base)
                else:
                    soup.append(soup.new_tag('head'))
                    soup.head.append(new_base)

            # 2. Strip CSP to allow Google Script
            for tag in soup.find_all('meta'):
                if tag.get('http-equiv', '').lower() == 'content-security-policy':
                    tag.decompose()
            
            # 3. Inject Google Translate Widget
            # We use the 'googtrans' cookie to auto-trigger the translation
            
            # Script to set cookie and init
            js_code = f"""
                document.cookie = "googtrans=/auto/{self.lang_code}; path=/";
                
                function googleTranslateElementInit() {{
                    new google.translate.TranslateElement({{
                        pageLanguage: 'auto', 
                        includedLanguages: '{self.lang_code}', 
                        layout: google.translate.TranslateElement.InlineLayout.SIMPLE,
                        autoDisplay: false, 
                        multilanguagePage: true
                    }}, 'google_translate_element');
                }}

                // Inject CSS to HIDE the banner explicitly
                // We do NOT remove the elements, just make them invisible/zero-size so the script keeps running.
                const hideStyle = document.createElement('style');
                hideStyle.innerHTML = `
                    .goog-te-banner-frame {{ display: none !important; visibility: hidden !important; height: 0 !important; width: 0 !important; opacity: 0 !important; }}
                    iframe[name="goog-te-banner-frame"] {{ display: none !important; visibility: hidden !important; height: 0 !important; width: 0 !important; }}
                    
                    /* Hide the wrapper div that might appear */
                    body > div.skiptranslate {{ display: none !important; visibility: hidden !important; height: 0 !important; }}
                    
                    body {{ top: 0px !important; position: static !important; margin-top: 0px !important; }}
                    
                    #goog-gt-tt, .goog-te-balloon-frame {{ display: none !important; }}
                    .goog-text-highlight {{ background: transparent !important; box-shadow: none !important; }}
                    font {{ background-color: transparent !important; box-shadow: none !important; }}
                    #google_translate_element {{ display: none !important; }}
                `;
                document.head.appendChild(hideStyle);

                // Active Camouflage: MutationObserver to maintain visibility state
                const observer = new MutationObserver(function(mutations) {{
                    const iframes = document.querySelectorAll('.goog-te-banner-frame, iframe[name="goog-te-banner-frame"]');
                    iframes.forEach(iframe => {{
                         if (iframe.style.display !== 'none') {{
                             iframe.style.display = 'none';
                             iframe.style.visibility = 'hidden';
                             iframe.style.height = '0px';
                         }}
                    }});
                    
                    // Reset body shift caused by Google
                    if (document.body.style.top !== '0px') {{
                        document.body.style.setProperty('top', '0px', 'important');
                        document.body.style.setProperty('position', 'static', 'important');
                        document.body.style.setProperty('margin-top', '0px', 'important');
                    }}
                }});
                observer.observe(document.documentElement, {{ attributes: true, childList: true, subtree: true }});

            """
            
            script_config = soup.new_tag('script')
            script_config.string = js_code
            soup.body.append(script_config)
            
            # The official script
            script_loader = soup.new_tag('script', src="https://translate.google.com/translate_a/element.js?cb=googleTranslateElementInit")
            soup.body.append(script_loader)
            
            # The target element (hidden)
            div_elem = soup.new_tag('div', id="google_translate_element", style="display:none;")
            soup.body.insert(0, div_elem)

            # Return the modified HTML!
            self.signals.finished.emit(str(soup))
            
        except Exception as e:
            self.signals.error.emit(str(e))

class TranslationSignals(QObject):
    finished = Signal(str)
    error = Signal(str)

class NewsReaderDialog(QDialog):
    def __init__(self, url=None, html_content=None, title="News", parent=None, target_language=None):
        super().__init__(parent)
        self.setWindowTitle("Secure Uplink")
        self.resize(1100, 800)
        self.setMinimumSize(600, 400) # Prevent inverting or confusing resize behavior
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True) # Enable hover tracking
        
        self.threadpool = QThreadPool.globalInstance()
        self.original_url = url
        self.active_translation_lang = None
        self.pending_lang = target_language # Store immediately!
        
        # Resizing / Dragging Logic
        self.dragging = False
        self.resizing = False
        self.resize_edge = 0 # Bitmask: 1=Left, 2=Top, 4=Right, 8=Bottom
        self.resize_margin = 15 # Larger margin for easier corner grabbing
        self.drag_position = QPoint()

        self.setup_ui(title)
        
        # Load Content
        if html_content:
            self.set_content(html_content)
        elif url:
            # Clean cookies to avoid stale Google Translate state
            self.web_view.page().profile().cookieStore().deleteAllCookies()
            self.web_view.load(QUrl(url))
            
        if self.pending_lang:
             self.lbl_title.setText(f"ESTABLISHING UPLINK ({self.pending_lang})...")

        # ANIMATION: Entry
        self.setWindowOpacity(0.0)
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(400)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.setEasingCurve(QEasingCurve.OutCubic)
        self.anim.start()

    def _get_resize_edge(self, pos):
        edge = 0
        rect = self.rect()
        
        if pos.x() < self.resize_margin: edge |= 1  # Left
        if pos.x() > rect.width() - self.resize_margin: edge |= 4 # Right
        if pos.y() < self.resize_margin: edge |= 2  # Top
        if pos.y() > rect.height() - self.resize_margin: edge |= 8 # Bottom
        
        return edge

    def _update_cursor(self, edge):
        if edge == 1 or edge == 4: # Left/Right
            self.setCursor(Qt.SizeHorCursor)
        elif edge == 2 or edge == 8: # Top/Bottom
            self.setCursor(Qt.SizeVerCursor)
        elif edge == 3 or edge == 12: # TopLeft (\) or BottomRight
            self.setCursor(Qt.SizeFDiagCursor)
        elif edge == 6 or edge == 9: # TopRight (/) or BottomLeft
            self.setCursor(Qt.SizeBDiagCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            edge = self._get_resize_edge(event.position())
            if edge != 0:
                self.resizing = True
                self.resize_edge = edge
                self.drag_position = event.globalPosition().toPoint()
                event.accept()
            elif event.position().y() < 70: # Header drag
                self.dragging = True
                self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()

    def mouseMoveEvent(self, event):
        if self.resizing:
            delta = event.globalPosition().toPoint() - self.drag_position
            geom = self.geometry()
            
            if self.resize_edge & 1: # Left
                geom.setLeft(geom.left() + delta.x())
            if self.resize_edge & 2: # Top
                geom.setTop(geom.top() + delta.y())
            if self.resize_edge & 4: # Right
                geom.setRight(geom.right() + delta.x())
            if self.resize_edge & 8: # Bottom
                geom.setBottom(geom.bottom() + delta.y())
            
            self.setGeometry(geom)
            self.drag_position = event.globalPosition().toPoint()
            event.accept()  
        elif self.dragging:
             self.move(event.globalPosition().toPoint() - self.drag_position)
             event.accept()
        else:
            # Update cursor on hover
            edge = self._get_resize_edge(event.position())
            self._update_cursor(edge)

    def mouseReleaseEvent(self, event):
        self.resizing = False
        self.dragging = False
        self.setCursor(Qt.ArrowCursor)

        
    def setup_ui(self, title):
        # Master Layout
        master_layout = QVBoxLayout(self)
        master_layout.setContentsMargins(10, 10, 10, 10) # Padding for visual breathing room
        
        # Styled Container
        self.container = QFrame()
        self.container.setObjectName("Container")
        self.container.setStyleSheet("""
            QFrame#Container {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-radius: 12px;
            }
        """)
        
        master_layout.addWidget(self.container)
        
        # Inner Layout
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header / Toolbar
        header = QWidget()
        header.setStyleSheet("""
            background-color: #0f172a; 
            border-bottom: 1px solid #1e293b;
            border-top-left-radius: 12px;
            border-top-right-radius: 12px;
        """)
        header.setFixedHeight(50)
        
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(15, 0, 15, 0)
        
        self.lbl_title = QLabel(title)
        self.lbl_title.setStyleSheet("color: #f8fafc; font-weight: bold; font-size: 14px; border: none;")
        
        # Controls
        self.btn_close = QPushButton("CLOSE TRANSMISSION")
        self.btn_close.setCursor(Qt.PointingHandCursor)
        self.btn_close.clicked.connect(self.close_animated)
        self.btn_close.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: 1px solid #dc2626;
                color: #ef4444;
                border-radius: 4px;
                padding: 5px 10px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background: rgba(220, 38, 38, 0.1);
            }
        """)
        
        header_layout.addWidget(self.lbl_title)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_close)
        
        layout.addWidget(header)
        
        # Progress Bar overlay
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(2)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("QProgressBar { border: none; background: #0f172a; } QProgressBar::chunk { background-color: #6366f1; }")
        layout.addWidget(self.progress_bar)
        
        # Web View
        self.web_view = QWebEngineView()
        # Webview corners are hard to round via CSS, clipping via mask usually needed, 
        # but simpler is to let it be square inside the rounded frame or rely on visual integration.
        # We will not mask it potentially causing artifacts, but try to blend bg.
        self.web_view.setStyleSheet("background-color: #1e293b;")
        
        # Configure Profile
        profile = self.web_view.page().profile()
        profile.setHttpUserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Optimize Performance & Privacy
        try:
            self.interceptor = WebInterceptor()
            profile.setUrlRequestInterceptor(self.interceptor)
        except Exception as e:
            print(f"Warning: Failed to set WebInterceptor: {e}")

        try:
            settings = self.web_view.settings()
            settings.setAttribute(QWebEngineSettings.PlaybackRequiresUserGesture, True) # Block heavy auto-play video
        except Exception as e:
             print(f"Warning: Failed to set WebEngineSettings: {e}")
        
        # Inject Cookie Auto-Accept & Hide Script
        self._inject_cookie_blocker()

        # SSL
        self.web_view.page().certificateError.connect(self._handle_cert_error)
        
        # Events
        self.web_view.page().loadProgress.connect(self.progress_bar.setValue)
        self.web_view.page().loadFinished.connect(self._on_load_finished)
        
        layout.addWidget(self.web_view)
        
    def _inject_cookie_blocker(self):
        # Create a user script that runs at 'DocumentCreation' (start)
        script = QWebEngineScript()
        script.setName("cookie_crusher")
        script.setInjectionPoint(QWebEngineScript.DocumentCreation)
        script.setWorldId(QWebEngineScript.MainWorld)
        script.setRunsOnSubFrames(True)
        
        source = """
        (function() {
            // 1. INVISIBLE SHIELD
            // Hide banners immediately so user never sees them waiting to be clicked
            var style = document.createElement('style');
            style.innerHTML = `
                #onetrust-banner-sdk, 
                .onetrust-pc-dark-filter, 
                #onetrust-consent-sdk,
                .cc-banner,
                #cookie-law-info-bar 
                { opacity: 0 !important; pointer-events: none !important; transition: none !important; }
            `;
            document.documentElement.appendChild(style);

            // Helper: The logic to find and click the button
            function attemptClick() {
                // 1. Direct ID (Fastest/Most common)
                var otBtn = document.getElementById('onetrust-accept-btn-handler');
                if (otBtn) { 
                    otBtn.click(); 
                    console.log("SC: Auto-clicked OneTrust (ID)");
                    return true; 
                }

                // 2. Text Search (Fallback)
                var buttons = document.querySelectorAll('button, a.btn, input[type="button"], div[role="button"]');
                for (var i = 0; i < buttons.length; i++) {
                     var btn = buttons[i];
                     if (btn.offsetParent === null) continue; // Skip hidden
                     
                     var t = (btn.innerText || btn.textContent).toLowerCase().trim();
                     if (t.includes('permitir todas') || 
                        t.includes('todos las cookies') ||
                        t.includes('cookies de marketing') ||
                        t.includes('aceptar todo') ||
                        t.includes('accept all') ||
                        t.includes('allow all') ||
                        t.includes('alle akzeptieren') ||
                        (t === 'aceptar' && btn.classList.contains('call-to-action')) ||
                        t === 'aceptar' ||
                        t === 'agree') {
                         
                         btn.click();
                         console.log("SC: Auto-clicked Cookies (Text: " + t + ")");
                         return true;
                     }
                }
                return false;
            }

            // 2. MUTATION OBSERVER: React INSTANTLY when the banner is added to DOM
            var observer = new MutationObserver(function(mutations) {
                attemptClick();
            });
            observer.observe(document.documentElement, { childList: true, subtree: true });

            // 3. AGGRESSIVE POLLING: Backup in case mutation is missed or for async loads
            // Check every 50ms for the first 5 seconds
            var checkCount = 0;
            var maxChecks = 100; 
            
            function fastPoll() {
                attemptClick();
                checkCount++;
                if (checkCount < maxChecks) {
                    setTimeout(fastPoll, 50);
                }
            }
            
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', fastPoll);
            } else {
                fastPoll();
            }
        })();
        """
        script.setSourceCode(source)
        self.web_view.page().scripts().insert(script)

    def close_animated(self):
        # Logic to animate out
        self.anim.setDirection(QPropertyAnimation.Backward)
        self.anim.setEndValue(1.0) # Ensure end is 1 so backward goes to 0
        self.anim.setStartValue(0.0) 
        # Actually standard usage: range 0-1. Forward=0->1. Backward=1->0.
        # So just switching direction is enough if we are at 1.
        self.anim.finished.connect(self.accept)
        self.anim.start()

    def start_translation(self, lang_code):
        self.pending_lang = lang_code
        self.lbl_title.setText("ESTABLISHING UPLINK...")
        
    def _handle_cert_error(self, error):
        error.ignoreCertificateError()
        return True

    def _on_load_finished(self, success):
        self.progress_bar.setVisible(False)
        
        if success:
             self._accept_cookies()

        # Check for pending translation
        if success and hasattr(self, 'pending_lang') and self.pending_lang:
            # Move to active state
            self.active_translation_lang = self.pending_lang
            self.pending_lang = None
            
            self.lbl_title.setText("SIGNAL ACQUIRED - DECODING...")
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0,0) 
            self.web_view.page().toHtml(self._process_html)
            
        elif not success:
             self.lbl_title.setText("CONNECTION FAILED")

    def _accept_cookies(self):
        # Inject script to click known "Accept" buttons with polling
        # The banner might load asynchronously, so we check multiple times.
        js_code = """
        (function() {
            var attempts = 0;
            var maxAttempts = 20; // 10 seconds of trying
            
            function tryAccept() {
                // 1. OneTrust (Standard ID)
                var otBtn = document.getElementById('onetrust-accept-btn-handler');
                if (otBtn) {
                    console.log("Found OneTrust button via ID");
                    otBtn.click();
                    return true;
                }
                
                // 2. Text Search (Robust for different languages)
                // We look for "Allow all", "Permitir todas", etc.
                var buttons = document.querySelectorAll('button, a.btn, input[type="button"], div[role="button"]');
                for (var i = 0; i < buttons.length; i++) {
                    var btn = buttons[i];
                    // Skip hidden buttons
                    if (btn.offsetParent === null) continue;
                    
                    var t = (btn.innerText || btn.textContent).toLowerCase().trim();
                    
                    if (t.includes('permitir todas') || 
                        t.includes('todos las cookies') ||
                        t.includes('cookies de marketing') ||
                        t.includes('aceptar todo') ||
                        t.includes('accept all') ||
                        t.includes('allow all') ||
                        t.includes('alle akzeptieren') ||
                        (t === 'aceptar' && btn.classList.contains('call-to-action')) || /* RSI specific class sometimes */
                        t === 'aceptar' ||
                        t === 'agree') {
                        
                        console.log("Found cookie button via text: " + t);
                        btn.click();
                        return true;
                    }
                }
                return false;
            }

            // Initial try
            if (tryAccept()) return;

            // Poll every 500ms
            var interval = setInterval(function() {
                attempts++;
                if (tryAccept() || attempts >= maxAttempts) {
                    clearInterval(interval);
                }
            }, 500);
        })();
        """
        self.web_view.page().runJavaScript(js_code)

    def _process_html(self, html):
        if not hasattr(self, 'active_translation_lang') or not self.active_translation_lang:
            return

        worker = PageTranslationWorker(html, self.active_translation_lang, self.original_url)
        worker.signals.finished.connect(self.set_content)
        worker.signals.error.connect(lambda e: self.lbl_title.setText(f"ERROR: {e}"))
        self.threadpool.start(worker)
        self.active_translation_lang = None

    def set_content(self, html):
        self.web_view.setHtml(html, QUrl("https://robertsspaceindustries.com"))
        self.lbl_title.setText("TRANSMISSION DECODED")
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 100)
        
    def set_loading(self, is_loading):
        pass # Compatibility
