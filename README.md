# Audio Synchronizer

Aplikacja okienkowa (Python + tkinter) do porównywania folderów z muzyką.
Pokazuje, których plików brakuje w folderze docelowym i które pliki są w nim
nadmiarowe. Działa na dwa sposoby:

- **Komputer → telefon z Androidem** (przez kabel USB i ADB),
- **dwa foldery na komputerze**.

Porównanie jest **jednokierunkowe**: folder źródłowy (na komputerze) jest wzorcem,
a program sprawdza, czy cel wygląda tak samo.

> **Stan projektu:** aktualnie aplikacja porównuje foldery i pokazuje liczbę
> brakujących i nadmiarowych plików. Kopiowanie brakujących plików oraz pytanie,
> co zrobić z nadmiarowymi (usunąć / zostawić), jest w trakcie budowy.
> Warstwa logiki (`audio_sync`) ma już gotowe operacje kopiowania i usuwania,
> brakuje tylko ich podpięcia w interfejsie.

## Jak to działa

1. Program wylistuje pliki audio (`.mp3`, `.m4a`, `.mp4`) w obu miejscach,
   razem z podfolderami.
2. Dla każdego pliku zapamiętuje jego **ścieżkę względną** względem wybranego
   folderu głównego, np. `ROCK/Zespół/Utwór.mp3`. Dzięki temu da się porównać
   foldery leżące w zupełnie różnych miejscach.
3. Porównuje dwa zbiory ścieżek (odejmowanie zbiorów):
   - **do skopiowania** = jest w źródle, brak w celu,
   - **nadmiarowe** = jest w celu, brak w źródle.
4. Pliki rozpoznaje **tylko po nazwie i położeniu**, nie po zawartości ani dacie.
   Dla biblioteki muzycznej, w której pliki po dodaniu się nie zmieniają, to
   w zupełności wystarcza i jest bardzo szybkie.

Telefon jest obsługiwany przez **ADB** (Android Debug Bridge), a nie przez zwykły
Eksplorator. Eksplorator widzi telefon przez protokół MTP, który nie jest
prawdziwym dyskiem i nie da się go otworzyć z poziomu Pythona. Dlatego aplikacja
ma własną przeglądarkę folderów telefonu.

## Wymagania

- **Windows 10 / 11** (aplikacja korzysta z elementów specyficznych dla Windowsa)
- **Python 3.9 lub nowszy** (testowane na 3.11) z biblioteką tkinter. Tkinter jest
  wbudowany w standardowe instalatory Pythona (python.org oraz Microsoft Store),
  żadne dodatkowe pakiety nie są potrzebne.
- **Git** (do pobrania repozytorium)
- Tylko do trybu telefonu:
  - telefon z **Androidem** i kabel USB, który przesyła dane (nie tylko ładuje),
  - **Android SDK Platform-Tools** (zawiera `adb.exe`).

## Instalacja

### 1. Pobierz repozytorium

```powershell
git clone https://github.com/<twoja-nazwa>/audio-synchronizer-gui.git
cd audio-synchronizer-gui
```

### 2. Utwórz wirtualne środowisko

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Jeśli PowerShell odmówi uruchomienia skryptu (execution policy), wpisz raz:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

i powtórz aktywację. Projekt nie ma zewnętrznych zależności, więc nie ma czego
instalować przez `pip`. Środowisko wirtualne to tylko dobra praktyka.

### 3. Uruchom

```powershell
py main.py
```

Tryb **dwóch folderów na komputerze** działa od razu. Do trybu telefonu potrzebna
jest jeszcze konfiguracja z kolejnej sekcji.

## Konfiguracja telefonu (tryb Komputer → telefon)

### Pobierz ADB

Pobierz **SDK Platform-Tools for Windows** ze strony Androida
(wyszukaj: *android platform-tools download*) i rozpakuj do wybranego folderu.
Zwróć uwagę, że po rozpakowaniu `adb.exe` leży zwykle w podfolderze
`platform-tools`.

W aplikacji wskażesz plik `adb.exe` przyciskiem **Wybierz...** przy polu ADB.
Możesz też dodać folder `platform-tools` do zmiennej środowiskowej `PATH`,
wtedy wystarczy domyślna wartość `adb`.

### Włącz debugowanie USB na telefonie

1. *Ustawienia → Informacje o telefonie → Informacje o oprogramowaniu*
   i stuknij 7 razy w **Numer kompilacji** (nazwy zależą od producenta).
2. Wejdź w *Ustawienia → Opcje programisty* i włącz **Debugowanie USB**.
3. Podłącz telefon kablem, odblokuj ekran i zaakceptuj okno
   **„Zezwolić na debugowanie USB?"**.
4. Sprawdź połączenie:

   ```powershell
   adb devices
   ```

   Przy telefonie powinien być status `device` (a nie `unauthorized` ani pusta
   lista).

Na niektórych telefonach (np. Samsung) może być potrzebny dodatkowo sterownik
producenta.

## Użycie

1. Wybierz tryb: **Komputer → telefon** albo **Dwa foldery na komputerze**.
2. W trybie telefonu wskaż `adb.exe`.
3. Wybierz **folder źródłowy** na komputerze.
4. Wybierz **cel**:
   - tryb telefonu: przyciskiem **Wybierz...** otwierasz przeglądarkę folderów
     telefonu (pamięć wewnętrzna i karta SD). Wchodzisz w foldery dwuklikiem,
     a wybór zatwierdzasz przyciskiem **Wybierz ten folder**,
   - tryb dwóch folderów: zwykły dialog wyboru folderu.
5. Kliknij **Porównaj**. Wynik pojawi się w pasku statusu na dole okna.

Źródło i cel powinny wskazywać odpowiadające sobie foldery (np. oba główne
foldery z muzyką), bo porównywane są ścieżki względne.

## Skrót na pulpicie (opcjonalnie)

Uruchamianie bez okna konsoli, przez `pythonw.exe` z wirtualnego środowiska:

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

Uruchom to z głównego folderu projektu. Jeśli skrót nic nie otwiera, odpal
`py main.py` w terminalu, żeby zobaczyć komunikat błędu.

Zamiast skrótu możesz zbudować samodzielny plik `.exe`:

```powershell
pip install pyinstaller
pyinstaller --noconsole --onefile --name AudioSynchronizer main.py
```

Wynik znajdziesz w `dist\AudioSynchronizer.exe`.

## Struktura projektu

```
audio-synchronizer-gui/
├── main.py                    # punkt startowy
├── audio_sync/                # logika, bez tkintera
│   ├── adb.py                 # rozmowa z telefonem przez adb.exe
│   ├── filters.py             # które pliki się liczą, normalizacja nazw
│   ├── models.py              # Plan: wynik porównania
│   ├── comparison.py          # compare(source, target)
│   └── storage/
│       ├── base.py            # interfejs Storage
│       ├── local.py           # folder na dysku komputera
│       └── phone.py           # folder na telefonie (ADB)
└── ui/                        # tylko okienka
    ├── app.py                 # główne okno
    ├── path_row.py            # wiersz: opis + pole + przycisk
    ├── phone_browser.py       # przeglądarka folderów telefonu
    └── background.py          # praca w osobnym wątku
```

Najważniejszy pomysł to interfejs **`Storage`**: „miejsce, w którym leżą pliki"
ma trzy operacje (`list_files`, `put`, `delete`). Folder na dysku i telefon to
dwie jego implementacje, więc porównanie nie musi wiedzieć, z czym pracuje.
Dodanie nowego rodzaju celu (np. serwera FTP) to jeden nowy plik w
`audio_sync/storage/`.

Pakiet `audio_sync` nie importuje niczego z `ui`, dzięki czemu logikę można
używać i testować bez okna.

## Rozwiązywanie problemów

| Objaw | Co sprawdzić |
|---|---|
| `Nie znaleziono ADB pod ścieżką: ...` | Wskaż `adb.exe` w polu ADB albo dodaj `platform-tools` do `PATH`. |
| `Nie wykryto autoryzowanego telefonu` | Podłącz telefon, odblokuj ekran, zaakceptuj okno debugowania USB. |
| `adb devices` pokazuje pustą listę | Sprawdź kabel (musi przesyłać dane), włączone debugowanie USB, sterownik producenta. |
| `adb devices` pokazuje `unauthorized` | Zaakceptuj okno na telefonie. W razie potrzeby: `adb kill-server`, a w Opcjach programisty „Odwołaj autoryzacje debugowania USB". |
| `ModuleNotFoundError` | Uruchamiaj `main.py` z folderu projektu i sprawdź, czy istnieją pliki `__init__.py` w `audio_sync/`, `audio_sync/storage/` i `ui/`. |
| `python` otwiera Microsoft Store | Włącz alias aplikacji w *Ustawienia → Aplikacje → Zaawansowane ustawienia aplikacji → Aliasy wykonywania aplikacji*, albo używaj `py`. |

## Ograniczenia

- Tylko Windows.
- Porównanie po nazwach i ścieżkach, bez sprawdzania zawartości plików.
- Rozpoznawane rozszerzenia: `.mp3`, `.m4a`, `.mp4` (lista w `audio_sync/filters.py`).
- Folder źródłowy zawsze jest na komputerze, a porównanie idzie tylko w jedną stronę.
- Ustawienia (ścieżki, lokalizacja ADB) nie są jeszcze zapamiętywane między uruchomieniami.

## Licencja

Do uzupełnienia (np. MIT).
