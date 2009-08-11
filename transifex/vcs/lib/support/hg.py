import mercurial.ui

ui = mercurial.ui.ui()
ui.setconfig('ui', 'interactive', 'off')
ui.setconfig('ui', 'quiet', 'on')