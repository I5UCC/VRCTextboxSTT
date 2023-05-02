### v1.4.1 Changelog
- removes the requirements of git being installed by using a portable instance.
    - If the portable instance doesnt exist, the locally installed version is used.

### v1.4.0 Changelog (This includes the Beta Changelog)
- Preloading the whisper model on startup, this should remove the increased latency on the first transcription.
- No redownloading of the program needed anymore! Download once, install once. You will get notified about new updates in TextboxSTT. 
- TextboxSTT now comes with a portable python instance, that means required dependencies are now installed when needed.
- Added default word replacements for things like *, !, ?, .
- The "Reset Settings" button now resets all settings and restarts the program. (Word Replacements and Emotes are kept)
- The ⟳ button now restarts the program completely instead of reloading.
- The hotkey used by TextboxSTT now ignores input whenever you hold a modifier (CTRL, SHIFT etc.)
- You can now record a whole hotkey instead of just one key.

### v1.3.1 Changelog

Fixes running into Rate limit issues when in mode "once". This fixes the issue of certain transcriptions not appearing in the Textbox.

### v1.3.0 Changelog
- Control some TextboxSTT parameters over OSC in VRChat. Following parameters can be controlled:
    - "use_kat" (boolean)
    - "use_textbox" (boolean)
    - "use_both" (boolean)
    - "mode" (OSC parameter name "stt_mode") (integer)
    - Add those parameters to your Expression Menu to control them.
- when adding a custom model for whisper, they are then saved in the settings, to remove one, select it and clear the textfield and press enter.
- Autocorrection for spelling in the Text to Text field. Supported languages are English, Polish, Turkish, Russian, Ukrainian, Czech, Portuguese, Greek, Italian, Vietnamese, French and Spanish.
- In mode "once_continuous" and "realtime", the program now tries to find sentence ends when transcriptions are taking too long, modifiable by the "max_transciption_time" setting for whisper.
- Silero Voice activity detection. Further adds voice activity detection to filter out pauses and static noise.
- obs only script, running "obs_only.exe" will run TextboxSTT in OBS only mode. with a simple console window and real time transcription.

### v1.2.0 Changelog
- Translation between languages, powered by M2M-100 using ctranslate2.
    - Translate between any of the ~100 languages supported.
    - Translation requires downloading the M2M-100 model into cache, which is another ~2GB.
    - Inference is done on CPU by default, you can change this but i would advise against it, unless you have another 2GB of VRAM to spare.
- Text timeout is now handled by TextboxSTT, for more consistency between KAT, Textbox and the SteamVR Overlay.
    - e.g. it will consistently populate the Textbox/KAT until either the Text timeout time is reached (30.0 seconds by default), or if it is cleared manually. Changing that value to <=0.0 will never clear the textbox, unless cleared manually.
- Changed the default "phrase_time_limit" from 2.0 to 1.0, for more "real time" transcriptions in modes "once_continuous" and "realtime"

### v1.1.3 Changelog
- Fixed obs not launching unless reloading the program.
- added a typewriter effect to the OBS Source for better readability.

### v1.1.2 Changelog
- Fixed context managing issue with audio source in mode once_continuous and realtime
- Try preventing SteamVR Overlay from freezing by switching Application type to Overlay and reinitializing OVR when error OverlayError_RequestFailed

### v1.1.1 Changelog
- Automatically restarting the program when it is needed.
- Fixed obs browser source not launching.
- Fixed whisper transcribing random words when its only noise. (maybe use VAD in the future to avoid this issue and generally better results with transcription)
- Refactor and logging changes and fixes.
- Reverted some default value changes

### v1.1.0 Changelog
- #2 allow use of user fine tuned models on [Huggingface](https://huggingface.co/models?sort=downloads&search=whisper)
   - translation to english does not work with those models, at least with my testing.
   - In the model section of the settings select "custom" and enter a path to a huggingface model: e.g. "openai/whisper-base": You can return to selection by pressing enter on an empty box.<br>

https://user-images.githubusercontent.com/43730681/227533337-82a076dc-e16a-4f31-a156-969477c02e93.mp4

- complete config revamp, same (and more) config options but more organized!
   - sadly for this version you cannot automatically take your old config with you, you can ask in the support discord on how to do that if you have alot of word replacements and/or emotes set.
- fast reload feature: click on the ⭯ button to quickly reload TextboxSTT
- added audio settings: added a gain slider and an individiual toggle for each audio feedback step. <br>
![image](https://user-images.githubusercontent.com/43730681/227530321-ba06a109-23a3-4eec-a638-27e5663b4063.png)
- Shows transcribe times in main UI now.
- better log management, the program creates up to 5 logs, "latest.log" is the latest. logs are now saved in the "cache" folder.
- added a program icon, wowee
- Seperate windows are now always positioning relative to the window that it was opened from, not on the main window.
- lots of refactoring and additional error logging.
- updated to faster-whisper 0.3.0
- some smaller bugfixes

### v1.0.0 Changelog
- Enforcing Single Instance by closing other instances of the program.
- Switched from pyinstaller to cx_freeze for distributing (again).
    - Files are much more organized and clearer.
- ***Switched from [openai/whisper](https://github.com/openai/whisper) to [guillaumekln/faster-whisper](https://github.com/guillaumekln/faster-whisper) !***
    - This implementation is up to ***4 times faster*** than [openai/whisper](https://github.com/openai/whisper) for the same accuracy while using less memory. ([Benchmarks](https://github.com/guillaumekln/faster-whisper#benchmark))
- Added additional device settings for transcription
    - "compute_type"
    - "cpu_threads"
    - "num_workers"
- Added Audio feedback toggle
- Some OBS source fixes.
- Delete cache after downloading model.
- logging transcribe times.
- You should now be able to take config.json files in between versions. Missing entries are added. Unused entries are removed.
- create config if it doesnt exist.
