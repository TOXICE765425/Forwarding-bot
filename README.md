<div align="center">

# 🧊 Forwarding Bot

### ⚡ Premium Telegram Video Parsing & Forwarding System

<p>
  <img src="https://img.shields.io/badge/UI-Glass%20Premium-8A2BE2?style=for-the-badge" alt="Glass Premium">
  <img src="https://img.shields.io/badge/Telegram-Bot-229ED9?style=for-the-badge&logo=telegram&logoColor=white" alt="Telegram">
  <img src="https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Firebase-Database-FFCA28?style=for-the-badge&logo=firebase&logoColor=black" alt="Firebase">
</p>

> 🎬 **Fast • Clean • Persistent • Multi-Language • Admin Controlled**

**Developer:** `Toxice Hacker`

</div>

---

## 🪟 ✨ Premium Glass Overview

<table>
<tr>
<td>

### 🎬 Video Engine
- 5 videos per normal user request
- 10-minute user cooldown
- Owner cooldown bypass
- Saved user position/progress
- Video copy without server-side downloading
- Protected content support
- Auto-delete support

</td>
<td>

### 🧠 Smart Control
- Video Parsing ON / OFF
- Persistent Firebase state
- User consent system
- Multi-language interface
- Profile-photo welcome
- Owner-only admin controls
- Detailed activity tracking

</td>
</tr>
</table>

---

## 🎥 Video Parsing Flow

```text
┌──────────────────────────────────────────────┐
│              🎬 VIDEO PARSING                │
├──────────────────────────────────────────────┤
│                                              │
│   👤 User                                    │
│      │                                       │
│      ▼                                       │
│   📜 Terms & Consent                         │
│      │                                       │
│      ▼                                       │
│   🎬 Video File                              │
│      │                                       │
│      ├── ⛔ Bot OFF → Status Message         │
│      │                                       │
│      └── ✅ Bot ON                           │
│              │                               │
│              ▼                               │
│       🔎 Search Sources                      │
│              │                               │
│              ▼                               │
│       📦 Copy 5 Videos                      │
│              │                               │
│              ▼                               │
│       💾 Save User Progress                 │
│                                              │
└──────────────────────────────────────────────┘
```

---

## 👑 Admin Control Center

### Main Admin Commands

| Command | Purpose |
|---|---|
| `/admin` | 👑 Open Admin Panel |
| `/help` | 📖 Full command guide |
| `/stats` | 📊 Bot statistics |
| `/user` | 👥 User list |
| `/activity USER_ID` | 🔎 User activity |
| `/bots` | 🤖 Bot/user information |
| `/broadcast` | 📢 Broadcast message |
| `/broadcast bot` | 📢 Broadcast alias |

### 🎬 Source Management

| Command | Purpose |
|---|---|
| `/source add CHAT_ID TITLE` | ➕ Add source |
| `/source remove CHAT_ID` | 🗑️ Remove source |
| `/source list` | 📂 Show sources |

### 🔌 Video Parsing Control

| Command | Purpose |
|---|---|
| `/bot on` | 🟢 Enable video parsing |
| `/bot off` | 🔴 Disable video parsing |
| `/bot status` | ℹ️ Check parsing status |

When parsing is disabled, users do **not** receive videos. They receive a localized status message instead.

---

## 🌍 Multi-Language System

The bot supports a broad set of languages, including:

🇮🇳 Hindi • Bhojpuri • English • Bengali • Telugu • Marathi • Tamil • Gujarati • Urdu • Kannada • Malayalam • Punjabi • Assamese • Maithili • Sanskrit • Nepali • Konkani • Sindhi • Dogri • Kashmiri • Manipuri • Bodo • Santali • Odia

Plus:

🇷🇺 Russian • 🇨🇳 Chinese • 🇯🇵 Japanese • 🇪🇸 Spanish • 🇫🇷 French • 🇩🇪 German • 🇵🇹 Portuguese • 🇸🇦 Arabic • 🇹🇷 Turkish • 🇮🇩 Indonesian • 🇻🇳 Vietnamese • 🇰🇷 Korean • 🇮🇹 Italian • 🇳🇱 Dutch • 🇵🇱 Polish • 🇺🇦 Ukrainian • 🇮🇷 Persian • 🇹🇭 Thai

> 🌐 User-facing parsing-off and system messages are localized according to the selected language.

---

## 💎 Premium Feature Matrix

| Feature | Status |
|---|:---:|
| 🎬 Video Parsing | ✅ |
| 📦 5 Videos / Request | ✅ |
| ⏱️ User Cooldown | ✅ |
| 👑 Owner Cooldown Bypass | ✅ |
| 🔄 Saved Progress | ✅ |
| 💾 Firebase Persistence | ✅ |
| 📜 Terms & Consent | ✅ |
| 🌐 Multi-Language | ✅ |
| 🇮🇳 Bhojpuri | ✅ |
| 👤 Profile Welcome | ✅ |
| 🔴 Bot ON/OFF | ✅ |
| 📊 Statistics | ✅ |
| 👥 User Management | ✅ |
| 🔎 Activity Tracking | ✅ |
| 📢 Broadcast | ✅ |
| 📂 Source Management | ✅ |
| 🧹 Auto Delete | ✅ |
| 🛡️ Protected Content | ✅ |
| 🚀 Render Ready | ✅ |
| 🐳 Docker Ready | ✅ |

---

## 🔐 Privacy & Access

- 👑 Administrative commands are restricted to the configured owner.
- 💾 User progress and activity can persist through Firebase.
- 🎬 Videos are copied through Telegram rather than being downloaded to the server.
- 🛡️ Protected-content mode can be enabled for sent media.
- 📜 Users must accept the Terms before accessing the video feature.

---

## 🚀 Deployment

### 1️⃣ Upload

Push the project files to your GitHub repository.

### 2️⃣ Render

Create/deploy the service using the included deployment configuration.

### 3️⃣ Environment

Keep your existing Render environment variables. Add any new variables only when required by your configuration.

### 4️⃣ Start

Deploy the latest commit and wait for the bot to connect.

---

## 🧊 Project Style

```text
                    ╭──────────────────────╮
                    │   🧊 TOXICE HACKER   │
                    │   PREMIUM BOT CORE   │
                    ╰──────────┬───────────╯
                               │
              ┌────────────────┼────────────────┐
              │                │                │
           🎬 Media          👑 Admin         🌐 i18n
              │                │                │
              └────────────────┼────────────────┘
                               │
                          💾 Firebase
                               │
                          ⚡ Telegram
```

---

<div align="center">

### 🛠️ Developed by **Toxice Hacker**

**Premium Telegram Automation • Video Parsing • Admin Control**

`Built with Python • Telegram • Firebase`

</div>
