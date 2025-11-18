import re


ALT_TAB_EXCLUDES = [
    (r'C:\Windows\SystemApps\ShellExperienceHost_',                     r'\ShellExperienceHost.exe'),
    (r'C:\Windows\SystemApps\InputApp',                                 r'\WindowsInternal.ComposableShell.Experiences.TextInput.InputApp.exe'),
    (r'C:\Windows\SystemApps',                                          r'\TextInputHost.exe'),

    (r'C:\Program Files\WindowsApps\Microsoft.Windows.Photos_',         r'\Microsoft.Photos.exe'),
    (r'C:\Program Files\WindowsApps\Microsoft.WindowsStore_',           r'\WinStore.App.exe'),
    (r'C:\Program Files\WindowsApps\Microsoft.Getstarted_',             r'\WhatsNew.Store.exe'),
    (r'C:\Program Files\WindowsApps\Microsoft.Getstarted_',             r'\WhatsNew.Store.exe'),
    (r'C:\Program Files\WindowsApps\Microsoft.Office.OneNote_',         r'\onenoteim.exe'),
    (r'C:\Program Files\WindowsApps\Microsoft.WindowsCalculator_',      r'\Calculator.exe'),
    (r'C:\Program Files\WindowsApps\Microsoft.ZuneVideo',               r'\Video.UI.exe'),
    (r'C:\Program Files\WindowsApps\Microsoft.Whiteboard',              r'\WhiteboardWRT.exe'),

    (r'C:\Program Files\WindowsApps',                                   r'\PeopleApp.exe'),
    (r'C:\Program Files\WindowsApps',                                   r'\Music.UI.exe'),
    (r'C:\Program Files\WindowsApps',                                   r'\Cortana.exe'),
    (r'C:\Program Files\WindowsApps',                                   r'\HxOutlook.exe'),

    (r'C:\Windows\System32\WWAHost.exe',                                ''),
    (r'C:\Windows\System32\ApplicationFrameHost.exe',                   ''),

    (r'C:\Windows\ImmersiveControlPanel\SystemSettings.exe',            ''),
]

ALT_TAB_EXCLUDES_PATTERN = re.compile(r'^(?:' + '|'.join(f"{re.escape(prefix)}.*{re.escape(postfix)}" for prefix, postfix in ALT_TAB_EXCLUDES) + r')$')
