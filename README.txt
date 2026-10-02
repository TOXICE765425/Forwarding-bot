FORWARDING BOT
==============================

Premium Telegram Video Parsing & Forwarding System

Developer: Toxice Hacker

CORE FEATURES
-------------
[+] 5 videos per normal user request
[+] 10-minute cooldown for normal users
[+] Owner cooldown bypass
[+] Persistent user position/progress
[+] Firebase user/activity persistence
[+] Terms & Consent system
[+] Multi-language support
[+] Bhojpuri language support
[+] Profile-photo welcome
[+] Video Parsing ON/OFF
[+] Admin Panel
[+] Detailed /help
[+] Statistics
[+] User management
[+] User activity
[+] Broadcast
[+] Source management
[+] Auto-delete
[+] Protected content
[+] Render ready
[+] Docker ready

ADMIN COMMANDS
--------------
/admin
/help
/stats
/user
/activity USER_ID
/bots
/broadcast
/broadcast bot

SOURCE COMMANDS
---------------
/source add CHAT_ID TITLE
/source remove CHAT_ID
/source list

VIDEO PARSING CONTROL
---------------------
/bot on
/bot off
/bot status

VIDEO FLOW
----------
User
  |
  v
Terms & Consent
  |
  v
Video File
  |
  +-- Bot OFF -> localized status message
  |
  +-- Bot ON
        |
        v
     Search sources
        |
        v
     Copy 5 videos
        |
        v
     Save progress

LANGUAGES
---------
Hindi, Bhojpuri, English, Bengali, Telugu, Marathi, Tamil,
Gujarati, Urdu, Kannada, Malayalam, Punjabi, Assamese, Maithili,
Sanskrit, Nepali, Konkani, Sindhi, Dogri, Kashmiri, Manipuri,
Bodo, Santali, Odia, Russian, Chinese, Japanese, Spanish, French,
German, Portuguese, Arabic, Turkish, Indonesian, Vietnamese,
Korean, Italian, Dutch, Polish, Ukrainian, Persian and Thai.

IMPORTANT
---------
- Admin commands are owner-only.
- Normal users have the cooldown; the owner bypasses it.
- Users must accept Terms before using the video feature.
- When parsing is OFF, users receive a localized status message
  instead of videos.
- Video media can be copied through Telegram without server-side
  video downloading.

DEVELOPER
---------
Toxice Hacker
