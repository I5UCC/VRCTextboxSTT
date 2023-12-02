# <img src="https://raw.githubusercontent.com/I5UCC/VRCTextboxSTT/main/src/resources/icon.ico" width="32" height="32"> TextboxSTT [![Github All Releases](https://img.shields.io/github/downloads/i5ucc/VRCTextboxSTT/total.svg)](https://github.com/I5UCC/VRCTextboxSTT/releases/latest) <a href='https://ko-fi.com/i5ucc' target='_blank'><img height='35' style='border:0px;height:25px;' src='https://az743702.vo.msecnd.net/cdn/kofi3.png?v=0' border='0' alt='Buy Me a Coffee at ko-fi.com' />

A SpeechToText application that uses [OpenAI's whisper](https://github.com/openai/whisper) via [faster-whisper](https://github.com/guillaumekln/faster-whisper) to transcribe audio and send that information to VRChats textbox system and/or [KillFrenzyAvatarText](https://github.com/killfrenzy96/KillFrenzyAvatarText) over OSC. Also supports OBS via Browsersource and a SteamVR overlay!
> [!NOTE]
> This program is designed to be completely free of charge, open source, and independent from Cloud-Based Transcription services such as Microsoft Azure. It accomplishes this by utilizing transcription algorithms that run on your own hardware, thereby upholding privacy, enhancing latency, and ensuring reliability. As a result, I will not be incorporating any cloud-based transcription or translation services into this program.

### [<img src="https://assets-global.website-files.com/6257adef93867e50d84d30e2/636e0a6ca814282eca7172c6_icon_clyde_white_RGB.svg"  width="20" height="20"> Discord Support Server](https://discord.gg/rqcWHje3hn)

### [🢃 Download Latest Release](https://github.com/I5UCC/VRCTextboxSTT/releases/latest)

# Features

- Sending transcription to either:
  - VRChats Ingame Textbox allowing for use with any avatar.
  - [KillFrenzyAvatarText (KAT)](https://github.com/killfrenzy96/KillFrenzyAvatarText) that needs to be integrated to an avatar. 
    - You can use [Frosty704's Billboard](https://github.com/Frosty704/Billboard) to add a speech bubble to your avatar.
    - Support for up to 80 emotes!
    - Automatic Detection of KAT on an avatar. It will use KAT if available, otherwise fall back to VRChat Textbox.
  - OBS over Browser Source!
  - Websockets
- ***SteamVR Overlay*** for seeing your transcription without having to look at your own textbox in-game.
- ***Fast and Efficient***. VRCTextboxSTT uses [ctranslate2](https://github.com/OpenNMT/CTranslate2) as the runtime for transcription and translation, which makes it incredibly efficient and fast.
- ***Uses Steam Input***, press to transcribe, hold to clear/cancel (A/X by default). Also works on desktop with the "F1" Key by default.
- ***Customizable***
  - You can bind the button to start transcription to any action that SteamVR allows you to set.
  - You can bind it to any key on your keyboard.
  - Many Timing settings for transcription delays and button presses.
  - Multiple different Transcription modes to choose from.
  - You can change all of the Audio feedback sounds to a sound of your liking.
- Ability to to use fine tuned models from [Huggingface](https://huggingface.co/models?sort=downloads&search=whisper)
- ***Automatic launch*** with SteamVR.
- ***Text to Text*** for quick typing.
- ***Simple API.*** latest transcription bound to the "/transcript" endpoint. (Requires OBS Source to be turned on)
- ***Audio feedback*** for each step in the transcription.
  - Volume for each of the feedbacks can be modified over the Settings menu.
- ***Multi Language support***. whisper supports around [100 different languages](https://github.com/openai/whisper/blob/main/whisper/tokenizer.py#L10). 
  - Translate into and from those different languages. (Powered by [M2M100](https://huggingface.co/docs/transformers/model_doc/m2m_100))
- Word Replacements and Emote Replacements with [Regular Expressions](https://en.wikipedia.org/wiki/Regular_expression).
- Free to use as of the [GPL-3.0 license](https://github.com/I5UCC/VRCTextboxSTT/blob/main/LICENSE)
- Completely free of Subscription/Cloud Services, by running locally on your hardware.
- Runs completely offline, besides downloading models/dependencies and updates/update checks

# Limitations

- Limited character availability
  - VRChats Textbox is limited to showing 144 characters at a time.
  - KillFrenzyAvatarText does support ASCII characters and a certain set of Japanese hiragana. <br>
    Limited to showing 128 characters at a time.
- Visibility
  - VRChats Textbox is only visible to friends by default, consider telling people they can change that in VRChats settings.
  - VRChats Textbox is not visibile in Streamer-Mode.
  - KillFrenzyAvatarText is only visible to shown avatars and is PC only, as it uses a custom shader setup.

# Requirements

With default settings, this program has following requirements:

- [.NET 4.8.1](https://dotnet.microsoft.com/en-us/download/dotnet-framework/thank-you/net481-web-installer) (***Should*** be preinstalled on Windows 10 and up)
- [Visual C++ 2015-2022 Redistributable (x64)](https://aka.ms/vs/17/release/vc_redist.x64.exe)
- SteamVR (IF ran in VR, no Oculus/Meta support as of now.)
- Inference on GPU (Recommended): 
  - CUDA enabled GPU (NVIDIA ONLY), otherwise it will fall back to using CPU.
  - ~11GB of available space for installation, ~6GB of space used after successful installation and loading models.
  - ~1GB of available RAM.
  - ~600MB of available VRAM.
- Inference on CPU:
  - ~4GB of available space for installation, ~2GB of space used after successful installation and loading models.
  - ~400MB of available RAM.

> [!NOTE]
> Depending on settings changed in the program those requirements can change exponentially.

# Demo

[Frosty704](https://github.com/Frosty704) using VRCTextboxSTT and [KillFrenzyAvatarText](https://github.com/killfrenzy96/KillFrenzyAvatarText) with their [Billboard](https://github.com/Frosty704/Billboard) project. More to that on their repository. <br>
![](https://user-images.githubusercontent.com/36753686/223066845-2eddf954-c953-4dd4-816c-e0fbb5684ec0.gif)

# [Documentation (In Progress)](https://github.com/I5UCC/VRCTextboxSTT/wiki)

# [Backlog](https://github.com/users/I5UCC/projects/1)

# Similar Projects

There are similar projects that already exist that you might want to consider using

- RabidCrab's STT incurs a monetary cost and relies on cloud-based transcription services, which inherently tend to be slower and less reliable compared to local transcription methods.
- [VRCWizard's TTS-Voice-Wizard](https://github.com/VRCWizard/TTS-Voice-Wizard) employs a wide array of transcription methods, encompassing both local and cloud-based approaches. Furthermore, it offers support similar to that of KAT, as seen in this project. Beyond functioning solely as a Speech To Text program, TTS-Voice-Wizard boasts a range of additional, noteworthy features. It may be worth your while to explore this tool further.
- [yum-food's TaSTT](https://github.com/yum-food/TaSTT) This project is spiritually and philosophically very close to this project, they have very feature rich avatar text solution that supports more characters then KAT does. They have made great progress on this problem, definitely take a look at it!

# Support this Project

You can always leave a Github Star 🟊 (It's free) or buy me a coffee:<br /> 

<a href='https://ko-fi.com/i5ucc' target='_blank'><img height='35' style='border:0px;height:35px;' src='https://az743702.vo.msecnd.net/cdn/kofi3.png?v=0' border='0' alt='Buy Me a Coffee at ko-fi.com' /><br />

# Credit
- [OpenAI](https://github.com/openai) for their amazing work with anything really.
- [guillaumekln/faster-whisper](https://github.com/guillaumekln/faster-whisper) and [ctranslate2](https://github.com/OpenNMT/CTranslate2), their work makes this project much more efficent and faster then it otherwise would be.
- [ValveSoftware/openvr](https://github.com/ValveSoftware/openvr) and [cmbruns/pyopenvr](https://github.com/cmbruns/pyopenvr)
- [Uberi/speech_recognition](https://github.com/Uberi/speech_recognition) and [jleb/pyaudio](https://github.com/jleb/pyaudio)
- [killfrenzy96](https://github.com/killfrenzy96) for [KillFrenzyAvatarText](https://github.com/killfrenzy96/KillFrenzyAvatarText) and [KatOSC](https://github.com/killfrenzy96/KatOscApp)
- [Frosty704's Billboard](https://github.com/Frosty704/Billboard) for making this project more useful.
- [cyberkitsune's OSCQuery implementation](https://github.com/cyberkitsune/tinyoscquery) because i was too lazy to do that myself xD
