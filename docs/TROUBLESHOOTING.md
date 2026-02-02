# 🔧 Troubleshooting Guide for Star Citizen Character Import

Common issues and solutions for managing your Star Citizen character DNA with BioMetrics.

## ⚠️ "Character Not Found" in Game

**Problem:** You installed a character, but it doesn't appear in the Character Customization screen inside Star Citizen.

**Solutions:**
1.  **Check Game Mode:** BioMetrics supports LIVE, PTU, and EPTU. Ensure you selected the correct environment in the settings.
2.  **Restart the Game:** Star Citizen loads character files at startup or when entering the character creator. A restart is often required.
3.  **Verify Path:** Go to `Settings` in BioMetrics and check if the *Star Citizen Installation Path* is correct (e.g., `C:\Program Files\Roberts Space Industries\StarCitizen`).

## 🚫 "Access Denied" Error

**Problem:** The application cannot write to the `CustomCharacters` folder.

**Solutions:**
1.  **Run as Administrator:** Right-click `SCCharacters.exe` and select "Run as Administrator".
2.  **Check Folder Permissions:** Ensure your Windows user has write permissions to the Star Citizen directory.
3.  **Antivirus Interference:** Add `SCCharacters.exe` to your antivirus exclusion list.

## 🧬 Corrupted Character File (.chf)

**Problem:** A character preset causes the game to crash or look distorted.

**Solutions:**
1.  **Delete the File:** In BioMetrics, go to the "Installed" tab and delete the problematic character.
2.  **Verify Integrity:** Use the "Verify Files" option in the RSI Launcher to repair your game installation if crashes persist.

## 🐞 Reporting Bugs

If your issue isn't listed here, please [open an issue on GitHub](https://github.com/Spieler1ONE1/SCCharacters/issues) with your log file attached.
