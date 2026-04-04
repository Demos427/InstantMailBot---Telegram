# Repository Analysis: InstantMailBot - Telegram

**Repository:** Demos427/InstantMailBot---Telegram
**Analysis Date:** April 4, 2026
**License:** MIT License (Copyright 2025 Demos)

---

## Executive Summary

This repository contains a fully automated Telegram bot that provides temporary email services. Users can generate disposable email addresses from multiple providers (Guerrilla Mail and Mail.tm) and receive emails directly in their Telegram chat. The bot features message history management and local data persistence.

---

## Repository Structure

```
InstantMailBot---Telegram/
├── .env                  # Configuration file for bot token
├── .git/                 # Git repository data
├── LICENSE               # MIT License
├── README.md             # User documentation
└── main.py              # Main bot application (366 lines)
```

**Generated at Runtime:**
- `comptes.json` - Stores user email account sessions
- `messages.json` - Stores received emails

---

## Technology Stack

### Programming Language
- **Python 3.x** (UTF-8 encoded, CRLF line terminators)

### Dependencies
```python
# Core Libraries
- python-telegram-bot[job-queue]  # Telegram bot framework
- aiohttp                          # Async HTTP client
- python-dotenv                    # Environment variable management
- brotli                           # Compression support

# Standard Libraries
- os, logging, json, asyncio
- random, string, datetime
```

---

## Core Architecture

### 1. Data Management (`JsonManager` class)

**Purpose:** Handles all data persistence using JSON files

**Key Methods:**
- `add_account()` - Creates new email account records
- `get_user_accounts()` - Retrieves user's email accounts
- `stop_account()` - Marks accounts as inactive
- `delete_account_data()` - Removes account and associated messages
- `save_message()` - Stores incoming emails (with duplicate detection)
- `get_messages_by_email()` - Retrieves messages for specific email
- `get_message_by_id()` - Fetches individual message details

**Data Structures:**

*Account Object:*
```json
{
  "user_id": int,
  "email": string,
  "service": string,
  "auth_data": object,
  "is_active": boolean,
  "created_at": ISO8601_timestamp
}
```

*Message Object:*
```json
{
  "id": int (timestamp in milliseconds),
  "email_address": string,
  "sender": string,
  "subject": string,
  "body": string,
  "received_at": "YYYY-MM-DD HH:MM:SS"
}
```

### 2. Email Service Architecture

**Abstract Base Class:** `EmailService`
- `create_account()` - Abstract method for account creation
- `get_messages()` - Abstract method for message retrieval

**Implemented Services:**

#### a) GuerrillaMailService
- **API:** https://api.guerrillamail.com/ajax.php
- **Authentication:** Session-based (sid_token)
- **Features:** Quick email generation, no registration
- **Message Format:** Provides mail excerpt with "..." suffix

#### b) MailTmService
- **API:** https://api.mail.tm
- **Authentication:** JWT Bearer tokens
- **Account Creation:**
  - Generates random username (10 chars: lowercase + digits)
  - Generates random password (12 chars: letters + digits)
  - Fetches available domains
  - Creates account and obtains token
- **Message Format:** Provides message intro text

---

## Bot Functionality

### Command Structure

1. **`/start`** and **`/history`**
   - Both trigger the main menu (handler reused)
   - Displays service selection and management options

2. **`/help`**
   - Shows command reference guide

### Interactive Menu System (Inline Keyboards)

**Main Menu (`/start`):**
- 🦍 Guerrilla - Create Guerrilla Mail account
- 🛡️ Mail.tm - Create Mail.tm account
- 🛑 Arrêter - Stop email monitoring
- 🗑️ Supprimer - Delete accounts/data
- 📂 Explorer Historique - Browse email history

**History Navigation:**
- Account selection → Message list → Message details
- Breadcrumb navigation with back buttons
- Shows message count per account

### Core Workflows

#### 1. Email Account Creation
```
User clicks service → Bot creates account → Bot starts monitoring job
↓
Monitoring job runs every 15 seconds
↓
New messages trigger Telegram notifications
```

#### 2. Message Monitoring
- **Job Scheduler:** `check_mail_job()` runs every 15 seconds
- **Duplicate Detection:** Prevents duplicate notifications
- **Error Handling:** Logs errors without crashing
- **Notification Format:**
  ```
  📨 Nouveau Mail!
  📬 {email}
  👤 {sender}
  📝 {subject}

  Aller dans /history pour lire le contenu complet.
  ```

#### 3. Account Management
- **Stop:** Removes monitoring job, marks account inactive
- **Delete:** Removes job + deletes all data (account + messages)

#### 4. History Explorer
- Three-level navigation:
  1. Account list with message counts
  2. Message list (truncated subjects, max 10)
  3. Full message view (truncated at 4000 chars for Telegram limits)

---

## Technical Features

### Asynchronous Operations
- All API calls use `async/await` with `aiohttp`
- Non-blocking HTTP requests
- Concurrent session management

### Job Queue System
- **Library:** python-telegram-bot JobQueue
- **Interval:** 15 seconds per email account
- **First Run:** 1 second for new accounts, 10 seconds for reloaded accounts
- **Job Naming:** `{user_id}_{email}` for easy identification
- **Persistence:** Reloads active accounts on bot restart (`post_init`)

### Error Handling
- Try-catch blocks for API operations
- JSON decode error handling
- File not found handling
- Graceful degradation on API failures

### Security Considerations

**Current Implementation:**
- ✅ Uses environment variables for sensitive tokens
- ✅ Stores data locally (no external database)
- ⚠️ No encryption for stored messages
- ⚠️ No authentication beyond Telegram user ID
- ⚠️ Token stored in plaintext in `.env`

**Potential Risks:**
- Messages stored in plain text JSON files
- No rate limiting on API calls
- No input validation on email addresses
- No sanitization of message content before display

---

## Code Quality Assessment

### Strengths
1. **Clean Architecture:** Well-separated concerns (DB, Services, Handlers)
2. **Extensible Design:** Easy to add new email services
3. **User Experience:** Interactive menu system with clear navigation
4. **Logging:** Proper logging configuration
5. **Error Recovery:** Handles missing files, JSON errors
6. **Resource Management:** Proper async session handling

### Areas for Improvement

1. **Code Documentation:**
   - No docstrings for classes/methods
   - Minimal inline comments
   - No type hints

2. **Error Handling:**
   - Generic exception catching in some places
   - Limited user feedback on errors
   - No retry mechanisms for failed API calls

3. **Configuration:**
   - Hardcoded polling interval (15 seconds)
   - No configurable message limits
   - Magic numbers throughout code

4. **Testing:**
   - No test files present
   - No CI/CD configuration
   - No test coverage

5. **Data Management:**
   - No database migration system
   - No data backup mechanism
   - No cleanup for old/inactive accounts

6. **Security:**
   - No input sanitization
   - No rate limiting
   - Messages stored in plaintext

---

## Localization

**Language:** French (Français)
- All user-facing messages in French
- Emoji-enhanced interface
- Date format: DD-MM-YYYY HH:MM:SS

**Sample Messages:**
- "Bienvenue. Que voulez-vous faire ?" (Welcome. What do you want to do?)
- "Nouveau Mail !" (New Mail!)
- "Arrêté" (Stopped)
- "Supprimé" (Deleted)

---

## Bot Lifecycle

### Initialization
1. Load environment variables (`.env`)
2. Initialize JSON manager (creates files if needed)
3. Build Telegram application
4. Register command handlers
5. Register callback query handler
6. Execute `post_init()` to reload active accounts
7. Start polling

### Runtime
1. User sends command → Handler processes → Response sent
2. User clicks button → Callback handler routes → Action performed
3. Background jobs check emails every 15 seconds
4. New messages saved and notifications sent

### Shutdown
- Graceful: Jobs stop automatically
- No explicit cleanup in code
- Data persists in JSON files

---

## API Integration Details

### Guerrilla Mail API
**Endpoint:** `https://api.guerrillamail.com/ajax.php`

**Methods Used:**
- `f=get_email_address` - Creates new temporary email
- `f=check_email&seq=0&sid_token={token}` - Checks for new messages

**Response Structure:**
```json
{
  "email_addr": "example@guerrillamail.com",
  "sid_token": "abc123...",
  "list": [
    {
      "mail_from": "sender@example.com",
      "mail_subject": "Subject",
      "mail_excerpt": "Preview text"
    }
  ]
}
```

### Mail.tm API
**Base URL:** `https://api.mail.tm`

**Endpoints Used:**
- `GET /domains` - List available domains
- `POST /accounts` - Create account
- `POST /token` - Authenticate and get JWT
- `GET /messages` - Retrieve messages (requires Bearer token)

**Authentication:** JWT Bearer token in Authorization header

---

## User Data Flow

```
User Action
    ↓
Telegram Update
    ↓
Command/Callback Handler
    ↓
Business Logic (Service/DB)
    ↓
API Call (if needed)
    ↓
Data Storage (JSON)
    ↓
Response to User
```

**Background Process:**
```
Job Scheduler (every 15s)
    ↓
API: Check Messages
    ↓
Compare with stored messages
    ↓
If new → Save + Notify user
```

---

## Deployment Notes

### Prerequisites
1. Python 3.7+ (for async/await support)
2. Telegram Bot Token from @BotFather
3. Internet connection for API access

### Setup Steps
1. Clone repository
2. Install dependencies: `pip install "python-telegram-bot[job-queue]" aiohttp python-dotenv brotli`
3. Create `.env` file with: `TELEGRAM_BOT_TOKEN=your_token_here`
4. Run: `python main.py`

### Runtime Requirements
- Continuous internet connection
- Read/write access to working directory (for JSON files)
- No special ports (uses Telegram's polling mechanism)

---

## Metrics and Statistics

- **Total Lines of Code:** 366
- **Classes:** 4 (JsonManager, EmailService, GuerrillaMailService, MailTmService)
- **Functions/Methods:** 20+
- **API Integrations:** 2 services
- **File Operations:** 2 JSON files
- **Commands:** 2 main commands + help
- **Callback Actions:** 10+ different button types

---

## Potential Enhancement Opportunities

1. **Functionality:**
   - Add more email service providers
   - Implement email attachment support
   - Add search/filter in message history
   - Support for HTML email rendering
   - Email forwarding capabilities

2. **User Experience:**
   - Add pagination for message lists
   - Implement message deletion
   - Add email marking (read/unread)
   - Configurable notification preferences
   - Multi-language support

3. **Technical:**
   - Add unit tests
   - Implement proper database (SQLite/PostgreSQL)
   - Add type hints (PEP 484)
   - Create configuration file for intervals/limits
   - Implement proper logging levels
   - Add health check endpoint
   - Create Docker containerization

4. **Security:**
   - Encrypt stored messages
   - Add rate limiting
   - Implement input sanitization
   - Add CAPTCHA support for email creation
   - Secure token storage

---

## Conclusion

This is a well-structured, functional Telegram bot that successfully provides temporary email services. The code demonstrates good architectural principles with clear separation of concerns, extensible design patterns, and effective use of async programming. While there's room for improvement in documentation, testing, and security, the current implementation provides a solid foundation for a temporary email service accessible through Telegram.

The bot is production-ready for personal/small-scale use but would benefit from enhancements in security, error handling, and testing before deployment at scale.

---

## File Inventory

| File | Purpose | Lines | Type |
|------|---------|-------|------|
| `main.py` | Core application | 366 | Python |
| `README.md` | User documentation | 41 | Markdown |
| `LICENSE` | MIT License | 22 | Text |
| `.env` | Configuration (token) | 2 | Text |
| `comptes.json` | Runtime (accounts) | Auto-generated | JSON |
| `messages.json` | Runtime (messages) | Auto-generated | JSON |

**Total Repository Size:** ~20 KB (excluding .git)
