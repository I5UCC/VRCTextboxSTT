# <img src="https://raw.githubusercontent.com/I5UCC/VRCTextboxSTT/main/src/resources/icon.ico" width="32" height="32"> VRCTextboxSTT [![Github All Releases](https://img.shields.io/github/downloads/i5ucc/VRCTextboxSTT/total.svg)](https://github.com/I5UCC/VRCTextboxSTT/releases/latest) <a href='https://ko-fi.com/i5ucc' target='_blank'><img height='35' style='border:0px;height:25px;' src='https://az743702.vo.msecnd.net/cdn/kofi3.png?v=0' border='0' alt='Buy Me a Coffee at ko-fi.com' />

A SpeechToText application that uses [OpenAI's whisper](https://github.com/openai/whisper) to transcribe audio and send that information to VRChats textbox system and/or [KillFrenzyAvatarText](https://github.com/killfrenzy96/KillFrenzyAvatarText) over OSC.

This program is supposed to be entirely free (as in money), open source and independent of Cloud Based Transcription services like Microsoft Azure etc., by using transcription Algorithms running on your own hardware, thus respecting privacy and improving latency and reliability, all at the cost of compromising a bit of performance by running on your own hardware. Therefore, I will not be implementing any Cloud Based transcription/translation etc.

### [<img src="https://assets-global.website-files.com/6257adef93867e50d84d30e2/636e0a6ca814282eca7172c6_icon_clyde_white_RGB.svg"  width="20" height="20"> Discord Support Server](https://discord.gg/rqcWHje3hn)

### [🢃 Download Latest Release](https://github.com/I5UCC/VRCTextboxSTT/releases/latest)

# Contents

- [Features](https://github.com/I5UCC/VRCTextboxSTT#features)
- [Limitations](https://github.com/I5UCC/VRCTextboxSTT#limitations)
- [Requirements](https://github.com/I5UCC/VRCTextboxSTT#requirements)
- [Demo](https://github.com/I5UCC/VRCTextboxSTT#demo)
- [How to use](https://github.com/I5UCC/VRCTextboxSTT#how-to-use)
- [OSC Troubleshoot](https://github.com/I5UCC/VRCTextboxSTT#osc-troubleshoot)
- [Configuration](https://github.com/I5UCC/VRCTextboxSTT#configuration)
- [Modifying SteamVR binding](https://github.com/I5UCC/VRCTextboxSTT#modifying-steamvr-binding)
- [Automatic launch with SteamVR](https://github.com/I5UCC/VRCTextboxSTT#automatic-launch-with-steamvr)
- [Backlog](https://github.com/I5UCC/VRCTextboxSTT#backlog)
- [Donate](https://github.com/I5UCC/VRCTextboxSTT#donate)
- [Credit](https://github.com/I5UCC/VRCTextboxSTT#credit)

# Features

- Sending transcription to either 
  - VRChats Ingame Textbox allowing for use with any avatar 
  - [KillFrenzyAvatarText (KAT)](https://github.com/killfrenzy96/KillFrenzyAvatarText) that needs to be integrated to an avatar. 
    - You can use [Frosty704's Billboard](https://github.com/Frosty704/Billboard) to add a speech bubble to your avatar.
    - Support for up to 80 emotes!
    - Automatic Detection of KAT on an avatar. It will use KAT if available, otherwise fall back to VRChat Textbox.
- ***Uses SteamVR binding system***, press to transcribe, hold to clear/cancel (A/X by default)
- ***Customizable***
  - You can bind the button to start transcription to any action that SteamVR allows you to set.
  - You can bind it to any key on your keyboard.
  - Many Timing settings for transcription delays and button presses.
- Optional ***Live Transcription***
- Optional ***Automatic launch*** with SteamVR.
- ***Text to Text*** for quick typing.
- Optional ***SteamVR Overlay*** for seeing your transcription without having to look at your own textbox in-game.
- Optional ***OBS Browser Source***.
- ***Simple REST-API.*** latest transcription bound to the "/transcript" endpoint. (Requires OBS Source to be turned on)
- ***Audio feedback*** for each step in the transcription.
- ***Multi Language support***. whisper supports around [100 different languages](https://github.com/openai/whisper/blob/main/whisper/tokenizer.py#L10). Here, with a few [limitations](https://github.com/I5UCC/VRCTextboxSTT#limitations).
- Translate into and from different languages. (Powered by [M2M100](https://huggingface.co/docs/transformers/model_doc/m2m_100)) (In next release)
- Word Replacements and Emote Replacements with regex(regular expressions).
- Free to use as of the [GPL-3.0 license](https://github.com/I5UCC/VRCTextboxSTT/blob/main/LICENSE)
- Completely free of Subscription/Cloud Services, by running locally on your hardware.


# Limitations

- Limited character availability
  - VRChats Textbox currently only supports ASCII characters, no support for Japanese, Korean etc. characters. <br>
    Limited to showing 144 characters at a time.
  - KillFrenzyAvatarText does support ASCII characters and a certain set of Japanese hiragana. <br>
    Limited to showing 128 characters at a time.
- Visibility
  - VRChats Textbox is only visible to friends by default, consider telling people they can change that in VRChats settings.
  - VRChats Textbox is not visibile in Streamer-Mode.
  - KillFrenzyAvatarText is only visible to shown avatars and is PC only, as it uses a custom shader setup.

# Requirements

With default settings, this program has following requirements:

- CPU version:
  - ~2GB of storage space.
  - ~400MB of available RAM.
- GPU version: 
  - CUDA enabled GPU (NVIDIA ONLY), otherwise it will fall back to using CPU.
  - ~5GB of storage space.
  - ~1GB of available RAM.
  - ~500MB of available VRAM.
- SteamVR (IF ran in VR, no Oculus/Meta support as of now.)

# Demo

[Frosty704](https://github.com/Frosty704) using VRCTextboxSTT and [KillFrenzyAvatarText](https://github.com/killfrenzy96/KillFrenzyAvatarText) with their [Billboard](https://github.com/Frosty704/Billboard) project. More to that on their repository. <br>
![](https://user-images.githubusercontent.com/36753686/223066845-2eddf954-c953-4dd4-816c-e0fbb5684ec0.gif)

# How to use


### Run from Releases
- Download one of the [Releases](https://github.com/I5UCC/VRCTextboxSTT/releases/latest).
- unpack the .7z file with a software of your choice.
- Run TextboxSTT.exe

### Run from source
- clone this repository, for example with git `git clone https://github.com/I5UCC/VRCTextboxSTT.git`
- Using python 3.10, install all of the dependencies from the requirements.txt file `python -m pip install -r requirements.txt`
- run the program by running `python main.py` in the projects directory

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
You can hover over any of the options to get a brief explanation on what that option does.
![image](https://user-images.githubusercontent.com/43730681/221786297-441951e0-771a-45e2-aaea-ea8d29c9ba52.png)

You can edit Word replacements by clicking the "Edit Word Replacements" button:

![image](https://user-images.githubusercontent.com/43730681/220126862-c398ffe6-8114-43de-ac76-6854f5e32217.png)

You can edit the emote settings by clicking the "Edit Emotes" button:

![image](https://user-images.githubusercontent.com/43730681/220127049-225f20b7-6153-4e93-8dc1-734f4414a935.png)

There are five model sizes, four with English-only versions, offering speed and accuracy tradeoffs. Below are the names of the available models and their approximate memory requirements and relative speed. 

|  Size  | Parameters | English-only model | Multilingual model | Required VRAM | Relative speed |
|:------:|:----------:|:------------------:|:------------------:|:-------------:|:--------------:|
|  tiny  |    39 M    |     `tiny.en`      |       `tiny`       |     ~1 GB     |      ~32x      |
|  base  |    74 M    |     `base.en`      |       `base`       |     ~1 GB     |      ~16x      |
| small  |   244 M    |     `small.en`     |      `small`       |     ~2 GB     |      ~6x       |
| medium |   769 M    |    `medium.en`     |      `medium`      |     ~5 GB     |      ~2x       |
| large  |   1550 M   |        N/A         |      `large`       |    ~10 GB     |       1x       |

For English-only applications, the `.en` models tend to perform better, especially for the `tiny.en` and `base.en` models. OpenAI observed that the difference becomes less significant for the `small.en` and `medium.en` models.

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
- ~~Add a quick entry box for quick messaging.~~
- ~~Create a Settings UI for easy config editing.~~
- ~~Enable Integration with [KillFrenzyAvatarText](https://github.com/killfrenzy96/KillFrenzyAvatarText).~~
- ~~Transcribe continuously until the user stops talking.~~
- ~~Add an emote feature~~
- ~~Demo Gif/Video (Stole from Frosty, thanks lol)~~
- ~~Add a OBS browsersource~~
- ~~Use [whisper.cpp](https://github.com/ggerganov/whisper.cpp)/[faster-whisper](https://github.com/guillaumekln/faster-whisper)for transcription, for better performance.~~
- ~~Allow use of finetuned models.~~
- Allow translation into and from different languages. M2M100 using ctranslate2 (Currently at work)
- Implement Text To Speech [silero-tts](https://github.com/snakers4/silero-models#speech-to-text) (Currently at work)

## Donate

You can always leave a Github Star 🟊 (It's free) or buy me a coffee:<br /> 

<a href='https://ko-fi.com/i5ucc' target='_blank'><img height='35' style='border:0px;height:35px;' src='https://az743702.vo.msecnd.net/cdn/kofi3.png?v=0' border='0' alt='Buy Me a Coffee at ko-fi.com' /><br />

# Credit
- [OpenAI](https://github.com/openai) for their amazing work with anything really.
- [guillaumekln/faster-whisper](https://github.com/guillaumekln/faster-whisper) for their really fast implementation of whisper.
- [ValveSoftware/openvr](https://github.com/ValveSoftware/openvr)
- [cmbruns/pyopenvr](https://github.com/cmbruns/pyopenvr)
- [Uberi/speech_recognition](https://github.com/Uberi/speech_recognition)
- [jleb/pyaudio](https://github.com/jleb/pyaudio)
- [pytorch](https://github.com/pytorch/pytorch)
- [killfrenzy96](https://github.com/killfrenzy96) for [KillFrenzyAvatarText](https://github.com/killfrenzy96/KillFrenzyAvatarText) and [KatOSC](https://github.com/killfrenzy96/KatOscApp)
- [Frosty704's Billboard](https://github.com/Frosty704/Billboard) for making this project more useful.
