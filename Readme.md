# Pulse Vector

**Pulse Vector** is an automated pipeline designed to organize and archive content into a structured library. It serves as a central hub for Current Affairs data and Brain Teasers, ensuring everything is filed neatly by date.

## 🚀 How It Works

The system operates on a simple **Drop & Run** mechanism:

1.  **Drop Files**: Place your raw text files (`.txt`) and Brain Teaser images (`.png`) into the **`incoming_data`** folder.
1.  **Drop Files**: Place your raw text files (`.txt`) and Brain Teaser images (`.png`) into the **`incoming_data`** folder.
2.  **Run Pipeline**: Execute the **`run_processor.sh`** script (or `python process_data.py`).
3.  **Done**: Your files are automatically processed, files into the **`pulse_archive`**, and **removed from the input folder** to save space.

## 📂 Project Structure

```text
pulse-vector/
├── incoming_data/       # <--- DROP YOUR FILES HERE
├── pulse_archive/       # <--- PROCESSED ARCHIVE
│   └── 2026/
│       └── January/
│           ├── Daily/
│           ├── Weekly/
│           ├── Monthly/
│           └── Brain_Teasers/
├── process_data.py      # The core sorting logic
└── run_processor.sh     # Execution script
```

## 🛠️ Supported Content

### 1. Current Affairs
The pipeline detects the following Date formats in your text file titles:
- **Daily**: `Daily Current Affairs 31 January 2026`
- **Weekly**: `Weekly Current Affairs ( 20-Oct-2026 - 26-Oct-2026 )`
- **Monthly**: `Monthly Current Affairs - (November, 2026)`

The content within these files is automatically formatted into a clean, numbered list.

### 2. Brain Teasers
Image files are automatically detected and sorted based on their filename:
- **Format**: `brainteaser-10jan26.png`
- **Sorted into**: `.../Year/Month/Brain_Teasers/`

## ⚙️ Usage

**Windows (Git Bash / WSL)**
```bash
bash run_processor.sh
```

**Windows (PowerShell/CMD)**
```powershell
python process_data.py
```