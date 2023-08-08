# <img src="https://raw.githubusercontent.com/I5UCC/VRCTextboxSTT/main/src/resources/icon.ico" width="32" height="32"> TextboxSTT [![Github All Releases](https://img.shields.io/github/downloads/i5ucc/VRCTextboxSTT/total.svg)](https://github.com/I5UCC/VRCTextboxSTT/releases/latest) <a href='https://ko-fi.com/i5ucc' target='_blank'><img height='35' style='border:0px;height:25px;' src='https://az743702.vo.msecnd.net/cdn/kofi3.png?v=0' border='0' alt='Buy Me a Coffee at ko-fi.com' />

A SpeechToText application that uses [OpenAI's whisper](https://github.com/openai/whisper) via [faster-whisper](https://github.com/guillaumekln/faster-whisper) to transcribe audio and send that information to VRChats textbox system and/or [KillFrenzyAvatarText](https://github.com/killfrenzy96/KillFrenzyAvatarText) over OSC. Also supports OBS via Browsersource and a SteamVR overlay!

This program is supposed to be entirely free (as in money), open source and independent of Cloud Based Transcription services like Microsoft Azure etc., by using transcription Algorithms running on your own hardware, thus respecting privacy and improving latency and reliability, all at the cost of compromising a bit of performance by running on your own hardware. Therefore, I will not be implementing any Cloud Based transcription/translation etc.

### [<img src="https://assets-global.website-files.com/6257adef93867e50d84d30e2/636e0a6ca814282eca7172c6_icon_clyde_white_RGB.svg"  width="20" height="20"> Discord Support Server](https://discord.gg/rqcWHje3hn)

### [🢃 Download Latest Release](https://github.com/I5UCC/VRCTextboxSTT/releases/latest)

# Contents

- [Features](https://github.com/I5UCC/VRCTextboxSTT#features)
- [Limitations](https://github.com/I5UCC/VRCTextboxSTT#limitations)
- [Requirements](https://github.com/I5UCC/VRCTextboxSTT#requirements)
- [Demo](https://github.com/I5UCC/VRCTextboxSTT#demo)
- [Installing and Updating TextboxSTT](https://github.com/I5UCC/VRCTextboxSTT#installing-and-updating-textboxstt)
- [How to use](https://github.com/I5UCC/VRCTextboxSTT#how-to-use)
- [OSC Troubleshoot](https://github.com/I5UCC/VRCTextboxSTT#osc-troubleshoot)
- [Configuration](https://github.com/I5UCC/VRCTextboxSTT#configuration)
- [Modifying SteamVR binding](https://github.com/I5UCC/VRCTextboxSTT#modifying-steamvr-binding)
- [Automatic launch with SteamVR](https://github.com/I5UCC/VRCTextboxSTT#automatic-launch-with-steamvr)
- [Backlog](https://github.com/I5UCC/VRCTextboxSTT#backlog)
- [Similar Projects](https://github.com/I5UCC/VRCTextboxSTT#similar-projects)
- [Donate](https://github.com/I5UCC/VRCTextboxSTT#donate)
- [Credit](https://github.com/I5UCC/VRCTextboxSTT#credit)

# Features

- Sending transcription to either:
  - VRChats Ingame Textbox allowing for use with any avatar.
  - [KillFrenzyAvatarText (KAT)](https://github.com/killfrenzy96/KillFrenzyAvatarText) that needs to be integrated to an avatar. 
    - You can use [Frosty704's Billboard](https://github.com/Frosty704/Billboard) to add a speech bubble to your avatar.
    - Support for up to 80 emotes!
  - OBS over Browser Source!
  - Automatic Detection of KAT on an avatar. It will use KAT if available, otherwise fall back to VRChat Textbox.
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

Depending on settings changed in the program those requirements can change exponentially.

# Demo

[Frosty704](https://github.com/Frosty704) using VRCTextboxSTT and [KillFrenzyAvatarText](https://github.com/killfrenzy96/KillFrenzyAvatarText) with their [Billboard](https://github.com/Frosty704/Billboard) project. More to that on their repository. <br>
![](https://user-images.githubusercontent.com/36753686/223066845-2eddf954-c953-4dd4-816c-e0fbb5684ec0.gif)

# Installing and Updating TextboxSTT

- Install the [Requirements](https://github.com/I5UCC/VRCTextboxSTT#requirements)

- Download and unpack this release of TextboxSTT

- Launch TextboxSTT.exe

- After first launch, the TextboxSTT Launcher will tell you that the program is not yet installed and asks you if you want to only install the CPU dependencies: <br>
![234649759-d70f5fb6-ef71-49c6-b84b-91e6530bb2e3](https://user-images.githubusercontent.com/43730681/235293653-f51b616d-ff45-4ffa-9599-7176c2ee70c8.png) <br>
After selecting an option (y = yes, n = no), ***No by default and recommended***, TextboxSTT will start installing all the dependencies needed. ***This only has to be done once***, after it will update dependencies whenever an update is available.
After the installation is done, TextboxSTT will start like normal. The first Startup might take a bit longer then usual.
To know whether an update is available, a button in the top right of the program will appear, informing you of a new update: <br>
![Updater](https://user-images.githubusercontent.com/43730681/234651576-fc79209d-1ba1-43a5-8fdd-b27816bc48ac.png) <br>
After clicking this button, the program will be updated and leads to a restart of the program. This process generally doesnt take much time.

# How to use

### Usage in VRChat
- Activate OSC in VRChat: <br/><br/>
![EnableOSC](https://user-images.githubusercontent.com/43730681/172059335-db3fd6f9-86ae-4f6a-9542-2a74f47ff826.gif)
- Run the program.
- The program will use your standard microphone set in windows.
- if you have a lot of background noise you should play around with the "energy_threshold" option in the configuration (or press the ⟳ button next to it), to get it working well.
- Press A on the left Controller on index or X on Oculus or F1 on your Keyboard.
- Holding any of those for 1.5s clears the chatbox or cancels the action.
- If the program doesnt work as its supposed to, try the troubleshooting steps in the next section.

## OSC Troubleshoot


If you have problems with this program, try this to fix it:<br><br>
1 - Close VRChat.<br>
2a - Press the "Reset OSC Settings" in the Settings of TextboxSTT<br>
2b - Open 'Run' in Windows (Windows Key + R). <br>
        Type in `%APPDATA%\..\LocalLow\VRChat\VRChat\OSC`<br>
       ㅤㅤ Delete the folders that start with 'usr_*'.<br>
3 - Startup VRChat again and it should work.

# Configuration

You can either Edit this configuration manually by editing the ***config.json*** file, or you can change those settings in the Program itself by clicking "Settings" in the bottom right: <br>
You can hover over any of the options to get a brief explanation on what that option does. <br>
![image](https://user-images.githubusercontent.com/43730681/232797308-5d2b38e4-dd00-4366-bd7b-e5fb3374edc0.png)

You can edit Word replacements by clicking the "Edit Word Replacements" button:

![image](https://user-images.githubusercontent.com/43730681/235309167-190135e9-024e-4bc2-a673-ce92db5e7833.png)

You can edit the emote settings by clicking the "Edit Emotes" button:

![image](https://user-images.githubusercontent.com/43730681/232797590-fbc99083-6c4d-4c46-8c10-89de5679ca10.png)

# Modifying SteamVR binding
You can set the boolean "sttlisten" in the Binding UI of SteamVR. Anyone who has set up OpenVR-Advanced-Settings might be familiar with that.
You can set it to any action that supports a boolean input. By default it is the left A button (X button on Oculus/Meta respectively).
![image](https://user-images.githubusercontent.com/43730681/210201138-d60d0936-22e5-4845-bbc1-4d1b0c412c43.png)

If you want to use a Chord, you have to create **empty actions** for the buttons you want to use for that chord and they will show up in the chrod menu: <br>
![image](https://user-images.githubusercontent.com/43730681/227457598-47b68d7b-3f4c-49d3-aa50-97c2b2bfeca7.png)
![image](https://user-images.githubusercontent.com/43730681/227457640-b2c3a55b-edad-4d66-84d7-5f331fe67ca4.png)

# Automatic launch with SteamVR
On first launch of the program, it registers as an Overlay app on SteamVR just like other well known programs like XSOverlay or OVRAdvancedSettings and can be launched on startup: <br>
![Screenshot 2022-12-04 184629](https://user-images.githubusercontent.com/43730681/205506892-0927ed45-69c6-480f-b4b3-bc02d89c151e.png) <br>
![Screenshot 2023-01-02 084823](https://user-images.githubusercontent.com/43730681/210209107-746196dd-7e19-47c4-a668-221824d44a4e.png)

After setting the option to ON it will launch the program on SteamVR startup.
If it doesnt show up, manually register the ´app.vrmanifest´ file by double clicking it and running it with SteamVR.

# Backlog
- [x] Add a quick entry box for quick messagin
- [x] Create a Settings UI for easy config editing.
- [x] Enable Integration with [KillFrenzyAvatarText](https://github.com/killfrenzy96/KillFrenzyAvatarText).
- [x] Transcribe continuously until the user stops talking.
- [x] Add an emote feature
- [x] Demo Gif/Video (Stole from Frosty, thanks lol)
- [x] Add a OBS browsersource
- [x] Use [whisper.cpp](https://github.com/ggerganov/whisper.cpp)/[faster-whisper](https://github.com/guillaumekln/faster-whisper) for transcription, for better performance.
- [x] Allow use of finetuned models.
- [x] Allow translation into and from different languages. M2M100 using ctranslate2
- [x] remove the need for building the program, enable OTA updates.
- [ ] Support [OSCQuery](https://github.com/vrchat-community/vrc-oscquery-lib)
- [ ] Implement Text To Speech (Maybe)
- [ ] Linux Support
- [ ] Documentation of features and code (In progress)

# Similar Projects

There are similar projects that already exist that you might want to consider using (or not)

- RabidCrab's STT. Costs Money, Uses cloud based transcription, the nature of that makes it typically slower and less reliable then local transcription methods.
- [VRCWizard's TTS-Voice-Wizard](https://github.com/VRCWizard/TTS-Voice-Wizard) uses a whole lot of different Transcription methods, both local and also cloud based. It also supports KAT like this project does. Moreover it has neat additional features that go over just being a Speech To Text program. You might want to take a look at this.
- [yum-food's TaSTT](https://github.com/yum-food/TaSTT) This project is spiritually and philosophically very close to this project, they have very feature rich avatar text solution that supports more characters then KAT does. They have made great progress on this problem, definitely take a look at it!

## Donate

You can always leave a Github Star 🟊 (It's free) or buy me a coffee:<br /> 

<a href='https://ko-fi.com/i5ucc' target='_blank'><img height='35' style='border:0px;height:35px;' src='https://az743702.vo.msecnd.net/cdn/kofi3.png?v=0' border='0' alt='Buy Me a Coffee at ko-fi.com' /><br />

# Credit
- [OpenAI](https://github.com/openai) for their amazing work with anything really.
- [guillaumekln/faster-whisper](https://github.com/guillaumekln/faster-whisper) and [ctranslate2](https://github.com/OpenNMT/CTranslate2), their work makes this project much more efficent and faster then it otherwise would be.
- [ValveSoftware/openvr](https://github.com/ValveSoftware/openvr) and [cmbruns/pyopenvr](https://github.com/cmbruns/pyopenvr)
- [Uberi/speech_recognition](https://github.com/Uberi/speech_recognition) and [jleb/pyaudio](https://github.com/jleb/pyaudio)
- [killfrenzy96](https://github.com/killfrenzy96) for [KillFrenzyAvatarText](https://github.com/killfrenzy96/KillFrenzyAvatarText) and [KatOSC](https://github.com/killfrenzy96/KatOscApp)
- [Frosty704's Billboard](https://github.com/Frosty704/Billboard) for making this project more useful.
