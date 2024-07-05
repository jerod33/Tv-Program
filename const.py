from datetime import timedelta

DOMAIN = "tv_program"
CONF_DAYS = "days"
CONF_TV_IDS = "tv_ids"
DEFAULT_TV_ID = ["4" , "2", "3", "1"]
DEVICE_CLASS_TIMESTAMP = "timestamp"
SCAN_INTERVAL = timedelta(hours=6)
USER_AGENT = 'SMSTVP/1.7.3 (242;cs_CZ) ID/ef284441-c1cd-4f9e-8e30-f5d8b1ac170c HW/Redmi Note 7 Android/10 (QKQ1.190910.002)'
BASE_URL = "http://programandroid.365dni.cz/android/v6-program.php"
