# Audio Synchronizer

A desktop app (Python + tkinter) for comparing music folders. It shows which
files are missing from the target folder and which files in it are extra.
It works in two ways:

- **Computer → Android phone** (over a USB cable, using ADB),
- **two folders on the computer**.

The comparison is **one-way**: the source folder (on the computer) is the
reference, and the program checks whether the target looks the same.

> **Project status:** the app currently compares folders and shows the number
> of missing and extra files. Copying the missing files and asking what to do
> with the extra ones (delete / keep) is still under construction. The logic
> layer (`audio_sync`) already has the copy and delete operations; they just
> aren't wired into the interface yet.
>
> Note: the app's interface is currently in Polish.

## How it works

1. The program lists the audio files (`.mp3`, `.m4a`, `.mp4`) in both places,
   including subfolders.
2. For each file it keeps the **relative path** from the chosen root folder,
   e.g. `ROCK/Band/Song.mp3`. This makes it possible to compare folders that
   live in completely different locations.
3. It compares the two sets of paths (set subtraction):
   - **to copy** = in the source, missing from the target,
   - **extra** = in the target, missing from the source.
4. Files are matched **by name and location only**, not by content or
   modification date. For a music library, where files don't change after
   they're added, that is plenty and very fast.

The phone is accessed through **ADB** (Android Debug Bridge), not through the
regular file explorer. Windows Explorer sees the phone over the MTP protocol,
which isn't a real drive and can't be opened from Python. That's why the app
has its own phone folder browser.

## Requirements

- **Windows 10 / 11** (the app uses Windows-specific features)
- **Python 3.9 or newer** (tested on 3.11) with tkinter. Tkinter is bundled with
  the standard Python installers (python.org and the Microsoft Store), and no
  extra packages are needed.
- **Git** (to clone the repository)
- Phone mode only:
  - an **Android** phone and a USB cable that carries data (not charge-only),
  - **Android SDK Platform-Tools** (contains `adb.exe`).

## Installation

### 1. Clone the repository

```powershell
git clone https://github.com/<your-username>/audio-synchronizer-gui.git
cd audio-synchronizer-gui
```

### 2. Create a virtual environment

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell refuses to run the script (execution policy), run this once:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

and activate again. The project has no external dependencies, so there is
nothing to install with `pip`. The virtual environment is just good practice.

### 3. Run

```powershell
py main.py
```

**Two folders on the computer** mode works right away. Phone mode needs the
setup described in the next section.

## Phone setup (Computer → phone mode)

### Get ADB

Download **SDK Platform-Tools for Windows** from the Android developer site
(search for: *android platform-tools download*) and extract it to any folder.
Note that after extracting, `adb.exe` is usually inside a `platform-tools`
subfolder.

In the app you point to `adb.exe` with the browse button next to the ADB field.
Alternatively, add the `platform-tools` folder to your `PATH` environment
variable, and then the default value `adb` is enough.

### Enable USB debugging on the phone

1. Go to *Settings → About phone → Software information* and tap **Build number**
   7 times (names vary by manufacturer).
2. Open *Settings → Developer options* and turn on **USB debugging**.
3. Connect the phone with a cable, unlock the screen and accept the
   **"Allow USB debugging?"** prompt.
4. Check the connection:

   ```powershell
   adb devices
   ```

   The phone should show the status `device` (not `unauthorized` and not an
   empty list).

Some phones (e.g. Samsung) may additionally need the manufacturer's USB driver.

## Usage

1. Pick a mode: **Computer → phone** or **Two folders on the computer**.
2. In phone mode, point to `adb.exe`.
3. Choose the **source folder** on the computer.
4. Choose the **target**:
   - phone mode: the browse button opens the phone folder browser (internal
     storage and SD card). Double-click to enter folders and confirm with
     **Select this folder**,
   - two-folder mode: a regular folder picker dialog.
5. Click the compare button. The result appears in the status bar at the
   bottom of the window.

The source and the target should point to corresponding folders (e.g. both
top-level music folders), because relative paths are what gets compared.

## Desktop shortcut (optional)

Launch without a console window, using `pythonw.exe` from the virtual
environment:

```powershell
$project = (Get-Location).Path
$desktop = [Environment]::GetFolderPath("Desktop")
$shell = New-Object -ComObject WScript.Shell
$lnk = $shell.CreateShortcut("$desktop\Audio Synchronizer.lnk")
$lnk.TargetPath = "$project\.venv\Scripts\pythonw.exe"
$lnk.Arguments = "main.py"
$lnk.WorkingDirectory = $project
$lnk.Save()
```

Run this from the project's root folder. If the shortcut opens nothing, run
`py main.py` in a terminal to see the error message.

Instead of a shortcut you can build a standalone `.exe`:

```powershell
pip install pyinstaller
pyinstaller --noconsole --onefile --name AudioSynchronizer main.py
```

The result is in `dist\AudioSynchronizer.exe`.

## Project structure

```
audio-synchronizer-gui/
├── main.py                    # entry point
├── audio_sync/                # logic, no tkinter
│   ├── adb.py                 # talking to the phone via adb.exe
│   ├── filters.py             # which files count, name normalization
│   ├── models.py              # Plan: the comparison result
│   ├── comparison.py          # compare(source, target)
│   └── storage/
│       ├── base.py            # the Storage interface
│       ├── local.py           # a folder on the computer's disk
│       └── phone.py           # a folder on the phone (ADB)
└── ui/                        # windows only
    ├── app.py                 # main window
    ├── path_row.py            # row: label + field + button
    ├── phone_browser.py       # phone folder browser
    └── background.py          # running work in a separate thread
```

The key idea is the **`Storage`** interface: "a place where files live" has
three operations (`list_files`, `put`, `delete`). A folder on disk and a phone
are two implementations of it, so the comparison doesn't need to know what it's
working with. Adding a new kind of target (e.g. an FTP server) means adding one
new file in `audio_sync/storage/`.

The `audio_sync` package imports nothing from `ui`, so the logic can be used
and tested without a window.

## Troubleshooting

| Symptom | What to check |
|---|---|
| `Nie znaleziono ADB pod ścieżką: ...` (ADB not found) | Point to `adb.exe` in the ADB field or add `platform-tools` to `PATH`. |
| "No authorized phone detected" (Polish: `Nie wykryto autoryzowanego telefonu`) | Connect the phone, unlock the screen, accept the USB debugging prompt. |
| `adb devices` shows an empty list | Check the cable (it must carry data), that USB debugging is on, and the manufacturer's driver. |
| `adb devices` shows `unauthorized` | Accept the prompt on the phone. If needed: `adb kill-server`, and in Developer options use "Revoke USB debugging authorizations". |
| `ModuleNotFoundError` | Run `main.py` from the project folder and check that `__init__.py` files exist in `audio_sync/`, `audio_sync/storage/` and `ui/`. |
| `python` opens the Microsoft Store | Turn on the app alias in *Settings → Apps → Advanced app settings → App execution aliases*, or use `py` instead. |

## Limitations

- Windows only.
- Comparison by names and paths, without checking file contents.
- Recognized extensions: `.mp3`, `.m4a`, `.mp4` (the list is in `audio_sync/filters.py`).
- The source folder is always on the computer, and the comparison only goes one way.
- Settings (paths, ADB location) aren't remembered between runs yet.

## License

To be added (e.g. MIT).
