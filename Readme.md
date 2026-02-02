# Pulse Vector

**Pulse Vector** is an intelligent, automated data pipeline designed to organize and archive educational content. It serves as a central engine for processing **Current Affairs** text data and **Brain Teaser** images, automatically sorting them into a structured, date-based hierarchy.

Stop manually creating folders. Just Drop & Run.

## 🚀 Key Features

*   **Automated Sorting**: Instantly organizes raw files into `Year > Month > Category` folders.
*   **Format Recognition**: Smartly detects dates and categories from filenames and file content.
*   **Content Formatting**: Automatically cleans and formats raw text lists into numbered entries.
*   **Zero-Dependency**: Built with standard Python libraries—no complex installation required.
*   **Dual Mode Support**: Works seamlessly on Windows (PowerShell/CMD) and Linux/WSL (Bash).

## 🤖 Automation & Architecture
The project runs on a daily automated pipeline triggered at 8:00 AM.
For a detailed visual flow of how the system works, please see [ARCHITECTURE.md](ARCHITECTURE.md).

## 📂 Project Structure

```text
pulse-vector/
├── incoming_data/       # [INPUT] Drop your raw .txt and .png files here
├── pulse_archive/       # [OUTPUT] The system organizes files here
│   └── 2026/
│       └── January/
│           ├── Daily/
│           ├── Weekly/
│           ├── Monthly/
│           └── Brain_Teasers/
├── process_data.py      # The core logic engine (Python)
├── run_processor.sh     # Convenience script for Bash users
└── Readme.md            # You are here
```

## 🛠️ Prerequisites

*   **Python 3.x** installed and added to your system PATH.
    *   Verify identification: `python --version`

No external Python packages (pip install) are required. The project uses standard libraries: `os`, `shutil`, `re`, `datetime`, `pathlib`.

## ⚙️ How to Use

### 1. Prepare Your Content
The system relies on specific naming patterns to identify where to file your data.

#### 📄 Current Affairs (Text Files)
Ensure the **first line** of your text file matches one of these formats:

| Category | Supported Title Formats (in first line) | Example |
| :--- | :--- | :--- |
| **Daily** | `Daily Current Affairs <Day> <Month> <Year>` | `Daily Current Affairs 31 January 2026` |
| | `Daily Current Affairs <DD><Mon><YYYY>` | `Daily Current Affairs 10Dec2025` |
| **Weekly** | `Weekly Current Affairs ( <Start> - <End> )` | `Weekly Current Affairs ( 20-Oct-2026 - 26-Oct-2026 )` |
| **Monthly** | `Monthly Current Affairs - (<Month>, <Year>)` | `Monthly Current Affairs - (November, 2026)` |

#### 🧩 Brain Teasers (Images)
Name your image files (`.png`) using this format:
*   **Format**: `brainteaser-<DD><mon><YY>.png`
*   **Example**: `brainteaser-10jan26.png`
*   **Example**: `sample-brain-teaser-05feb26.png`

### 2. Drop Files
Place all your prepared `.txt` and `.png` files into the **`incoming_data`** folder.

### 3. Run the Pipeline
Execute the processor script.

**On Windows (PowerShell / Command Prompt):**
```powershell
python process_data.py
```

**On Linux / macOS / Git Bash:**
```bash
bash run_processor.sh
```

### 4. Check Results
*   **Success**: Files are moved to `pulse_archive/`, organized by date.
*   **Cleanup**: One successfully archived, the original file is removed from `incoming_data` to keep your workspace clean.
*   **Errors**: Check the console output. If a file is skipped, verify the date format pattern matches the examples above.

## 🤝 Contributing
Feel free to fork this project and submit Pull Requests.
Common improvements include:
*   Adding support for `.jpg` or `.pdf` files.
*   Expanding the Regex patterns for more loose date matching.

---
*Maintained by the Pulse Vector Team*