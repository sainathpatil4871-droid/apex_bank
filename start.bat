@echo off
cd /d "%~dp0"
echo Installing requirements (first run only)...
python -m pip install -q -r requirements.txt || py -3 -m pip install -q -r requirements.txt
python server.py || py -3 server.py
pause
