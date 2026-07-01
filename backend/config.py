# backend/config.py

RECORDING_PROCESSES = [
    "obs64.exe", "obs32.exe", "obs.exe",
    "zoom.exe", "zoomus.exe",
    "teams.exe", "msteams.exe",
    "discord.exe", "discordptb.exe",
    "anydesk.exe", "teamviewer.exe",
    "bandicam.exe", "fraps.exe", "loom.exe",
    "skype.exe", "slack.exe",
    "gamebar.exe", "gamebarftserver.exe",
    "xboxgamebartaskwidgetserver.exe",
    "chrome.exe", "msedge.exe", "firefox.exe",
]

SCAN_INTERVAL = 0.5
FLASK_PORT    = 5001
FORCE_SCAN    = True