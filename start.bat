@echo off
chcp 65001 >nul
echo ============================================
echo  Steam Support Dashboard - Uruchamianie
echo ============================================
echo.

REM Sprawdz czy Python jest dostepny
python --version >nul 2>&1
if errorlevel 1 (
    echo [BLAD] Python nie jest zainstalowany lub nie jest dodany do zmiennej PATH.
    echo Pobierz Python ze strony: https://www.python.org/downloads/
    echo Podczas instalacji zaznacz opcje "Add Python to PATH"!
    echo.
    pause
    exit /b 1
)

echo [OK] Znaleziono Python.

REM Stworz venv jesli nie istnieje
if not exist "venv\Scripts\activate.bat" (
    echo [INFO] Tworzenie srodowiska wirtualnego. Pierwsze uruchomienie, chwile poczekaj...
    python -m venv venv
    if errorlevel 1 (
        echo [BLAD] Nie udalo sie stworzyc srodowiska wirtualnego.
        pause
        exit /b 1
    )
    echo [OK] Srodowisko wirtualne zostalo stworzone.
)

REM Aktywuj venv
echo [INFO] Aktywacja srodowiska wirtualnego...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [BLAD] Nie udalo sie aktywowac srodowiska wirtualnego.
    pause
    exit /b 1
)

REM Zainstaluj zaleznosci
echo [INFO] Sprawdzanie i instalowanie zaleznosci...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [BLAD] Nie udalo sie zainstalowac wymaganych bibliotek.
    echo Sprawdz plik requirements.txt i polaczenie z internetem.
    pause
    exit /b 1
)
echo [OK] Wszystkie zaleznosci sa zainstalowane.

echo.
echo [INFO] Uruchamianie aplikacji Streamlit...
echo [INFO] Aby zatrzymac aplikacje, nacisnij CTRL+C w tym oknie.
echo.
streamlit run app.py

pause
