# Claude AI Assistant Rules for This Project

## File Creation Rules

**IMPORTANT**: 

- ✅ **DO**: Create all documentation, scripts, and project files ONLY on the Raspberry Pi (pi-5-1)
- ❌ **DO NOT**: Create any documentation or project files on the Mac (/Users/shreyashgupta/)
- 📝 The Mac may have temporary working copies, but the ONLY authoritative location is the Raspberry Pi

### File Locations

**Raspberry Pi (pi-5-1) - PRIMARY LOCATION**
- Project directory: ~/voice_transcribe/
- All documentation: ~/voice_transcribe/*.md
- All scripts: ~/voice_transcribe/*.py

**Mac - DO NOT USE FOR PROJECT FILES**
- The Mac is used for SSH access only
- Do not create .md files on the Mac
- Do not create project files on the Mac
- Only the Raspberry Pi should have project files

## Project Structure

This is the voice transcription project using:
- Raspberry Pi 5
- INMP441 I2S microphone
- Faster-Whisper for speech-to-text
- Python 3.13

## Remember

When the user asks for documentation, scripts, or any project files, always create them on the Raspberry Pi at ~/voice_transcribe/, never on the Mac.

---

This file helps Claude remember project-specific rules and context.
