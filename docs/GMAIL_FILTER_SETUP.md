# Pulse Vector - Gmail Rules & Filter Setup Guide

This guide details the automated categorization, hierarchical Gmail labels, and filter rules configured for all Pulse Vector automated emails.

---

## 📊 1. Mail Audit & Current Inventory

An inspection of incoming and outbound automated emails across Gmail (`addytiwari3@gmail.com`) identified the following categories:

| Category | Email Subject Pattern | Source / Sender | Count in Inbox | Prior Status | New Label Applied |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Weekly Reports** | `[Pulse Vector] Weekly Executive Report — ...` | `Pulse Vector Automation` (`addytiwari3@gmail.com`) | **12** | Raw in Inbox (No label) | `Pulse Vector/Weekly Reports`<br>`Pulse Vector` |
| **Monthly Reports** | `[Pulse Vector] Monthly Executive Report — ...` | `Pulse Vector Automation` (`addytiwari3@gmail.com`) | **3** | Raw in Inbox (No label) | `Pulse Vector/Monthly Reports`<br>`Pulse Vector` |
| **General / Custom Reports** | `[Pulse Vector] ...` | `Pulse Vector Automation` (`addytiwari3@gmail.com`) | **0** | — | `Pulse Vector` |
| **GitHub Actions Alerts** | `[tiwari17aditya/pulsevector] ...` | `GitHub` (`support@github.com`, `notifications@github.com`) | **1** | Raw in Inbox (No label) | `Pulse Vector/Alerts`<br>`Pulse Vector/GitHub Actions` |

---

## 🏷️ 2. Hierarchical Gmail Labels Created

The following label hierarchy was created directly in your Gmail account via IMAP:

```text
📁 Pulse Vector
   ├── 📂 Weekly Reports       (Weekly executive performance & reach reports)
   ├── 📂 Monthly Reports      (Monthly executive breakdowns & analytics)
   ├── 📂 Alerts               (GitHub CI/CD failures, secret alerts, critical pipeline stops)
   └── 📂 GitHub Actions       (Automated workflow run logs & status notices)
```

All **16 existing emails** currently in your inbox have already been labeled and filed into their corresponding folders.

---

## ⚡ 3. 1-Click Filter Rule Import (`pulse_vector_gmail_filters.xml`)

All filter entries include:
- **Skip the Inbox (Archive it)** (`<apps:property name='shouldArchive' value='true'/>`)
- **Never mark it as important** (`<apps:property name='shouldNeverMarkAsImportant' value='true'/>`)
- **Never send to Spam** (`<apps:property name='shouldNeverSpam' value='true'/>`)

This maintains 100% inbox hygiene: all automated Pulse Vector emails silently route directly into their respective label folders without cluttering your inbox or triggering importance flags:

1. Open **[Gmail](https://mail.google.com/)** in your web browser.
2. Click the **Settings (⚙️)** gear icon in the top right corner and select **See all settings**.
3. Go to the **Filters and Blocked Addresses** tab.
4. Scroll down to the bottom and click **Import filters**.
5. Click **Choose File**, select `pulse_vector_gmail_filters.xml` from the root of your `pulse-vector` repository, and click **Open file**.
6. Check **Apply to existing conversations** and click **Create filters**.

---

## 🛠️ 4. Maintenance Script

If you ever want to re-scan your mailbox and retroactively label newly arrived emails, run:

```bash
python scripts/organize_gmail_labels.py
```
