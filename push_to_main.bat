@echo off
echo ===================================================
echo AgriRoute Intelligence - Pushing to GitHub (main)
echo ===================================================
echo.
git push -u origin main
echo.
if %ERRORLEVEL% EQU 0 (
    echo [SUCCESS] Successfully pushed to origin main!
) else (
    echo [ERROR] Push encountered an issue. See details above.
)
pause
