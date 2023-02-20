# VRCTextboxSTT [![Github All Releases](https://img.shields.io/github/downloads/i5ucc/VRCTextboxSTT/total.svg)](https://github.com/I5UCC/VRCTextboxSTT/releases/latest) <a href='https://ko-fi.com/i5ucc' target='_blank'><img height='35' style='border:0px;height:25px;' src='https://az743702.vo.msecnd.net/cdn/kofi3.png?v=0' border='0' alt='Buy Me a Coffee at ko-fi.com' />
### A SpeechToText application that uses [OpenAI's whisper](https://github.com/openai/whisper) to transcribe audio and send that information to VRChats textbox system and/or [KillFrenzyAvatarText](https://github.com/killfrenzy96/KillFrenzyAvatarText) over OSC.

### This program is supposed to be entirely free (as in money) and independent of Cloud Based Transcription services like Microsoft Azure etc., by using transcription Algorithms running on your own hardware, thus respecting privacy and improving latency and reliability, all at the cost of compromising a bit of performance by running on your own hardware.

# [Download Here](https://github.com/I5UCC/VRCTextboxSTT/releases/latest)

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
- [Credit](https://github.com/I5UCC/VRCTextboxSTT#credit)

# Features

- Sending transcription to either 
  - VRChats Ingame Textbox allowing for use with any avatar 
  - [KillFrenzyAvatarText (KAT)](https://github.com/killfrenzy96/KillFrenzyAvatarText) that needs to be integrated to an avatar. 
    - You can use [Frosty704's Billboard](https://github.com/Frosty704/Billboard) to add a speech bubble to your avatar.
- Automatic Detection of KAT on an avatar. It will use KAT if available, otherwise fall back to VRChat Textbox.
- Customizable button
  - You can bind the button to start transcription to any action that SteamVR allows you to set.
  - You can bind it to any key on your keyboard.
- Optional automatic launch with SteamVR.
- Optional Text to Text for quick typing.
- Audio feedback for each step in the transcription.
- Multi Language support. whisper supports around [100 different languages](https://github.com/openai/whisper/blob/main/whisper/tokenizer.py#L10). Here, with a few [limitations](https://github.com/I5UCC/VRCTextboxSTT#limitations).
- Free to use as of the [GPL-3.0 license](https://github.com/I5UCC/VRCTextboxSTT/blob/main/LICENSE)

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
  - ~1GB of available RAM.
- GPU version: 
  - CUDA enabled GPU (NVIDIA ONLY), otherwise it will fall back to using CPU.
  - ~5GB of storage space.
  - ~1GB of available RAM.
  - ~1GB of available VRAM.
- SteamVR (IF ran in VR, no Oculus support as of now.)

# Demo

[Frosty704](https://github.com/Frosty704) using VRCTextboxSTT and [KillFrenzyAvatarText](https://github.com/killfrenzy96/KillFrenzyAvatarText) with their [Billboard](https://github.com/Frosty704/Billboard) project. More to that on their repository.
![](https://user-images.githubusercontent.com/36753686/216971733-6301f273-8c52-4b9c-a8ff-d9d440a2e3d0.gif)

# How to use

- Activate OSC in VRChat: <br/><br/>
![EnableOSC](https://user-images.githubusercontent.com/43730681/172059335-db3fd6f9-86ae-4f6a-9542-2a74f47ff826.gif)
- Run the program.
- The program will use your standard microphone set in windows.
- if you have a lot of background noise you should play around with the "energy_threshold" option in the configuration (or press the ⟳ button next to it), to get it working well.
- Press A on the left Controller on index or X on Oculus or F1 on your Keyboard.
- Holding any of those for 1.5s clears the chatbox or cancels the action.

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
![image](https://user-images.githubusercontent.com/43730681/220126409-be4eabb9-2a93-4fc7-b747-aff5188c065d.png)

You can edit Word replacements by clicking the "Edit Word Replacements" button:

![image](https://user-images.githubusercontent.com/43730681/220126862-c398ffe6-8114-43de-ac76-6854f5e32217.png)

You can edit the emote settings by clicking the "Edit Emotes" button:

![image](https://user-images.githubusercontent.com/43730681/220127049-225f20b7-6153-4e93-8dc1-734f4414a935.png)

## config.json

| Option | Values | Default | Explanation |
|:------:|:------:|:-------:|:-----------:|
| "IP" | Any IP-Adress | "127.0.0.1" | IP to send the OSC information to. |
| "Port" | Any Port | 9000 | Port to send the OSC information to. |
| "osc_server_port" | Any Port | 9001 | Port to get the OSC information from. Used to improve KAT sync with in-game avatar and autodetect sync parameter count used for the avatar." |
| "model" | "tiny", "base", "small", "medium", "large" | base | What model of whisper to use. I'd recommend not going over "base" as it will significantly impact the performance |
| "language" | "english", "german", "spanish", "" | english | Language to use, "english" will be faster then other languages. Leaving it empty "", will let the program decide what language you are speaking. |
| "hotkey" | Any key supported by the [python keyboard library](https://github.com/boppreh/keyboard) | F1 | The key that is used to trigger listening. |
| "mode" | 0, 1, 2 | 0 | Transcribe mode to use 0 = once, 1 = once_continuous, 2 = realtime
| "dynamic_energy_threshold" | true, false | false | With dynamic_energy_threshold set to 'True', the program will continuously try to re-adjust the energy threshold to match the environment based on the ambient noise level at that time. I'd recommend setting the 'energy_threshold' value high when enabling this setting. |
| "energy_threshold" | 0-3500 | 200 | Under 'ideal' conditions (such as in a quiet room), values between 0 and 100 are considered silent or ambient, and values 300 to about 3500 are considered speech. |
| "pause_threshold" | 0.0- | 0.8 | Amount of seconds to wait when current energy is under the 'energy_threshold' |
| "timeout_time" | 0.0- | 3.0 | Amount of time to wait for the user to speak before timeout |
| "hold_time" | 0.0- | 1.5 | amount of time to hold the button to clear the Textbox |
| "phrase_time_limit" | 0.0- | 2.0 | The maximum number of seconds that this will allow a phrase to continue before stopping and returning the part of the phrase processed before the time limit was reached |
| "max_transcribe_time" | 0.0- | 0.0 | maximum amount of time for transcribing a message before transcribing gets cancelled. 0.0 is infinite |
| "microphone_index" | null, 0-10 | null | Index of the microphone to use. null is the System Default mircophone. |
| "word_replacements" | {"word1": "replacement1", "word2": "replacement2"} | {} | Array of banned words that are gonna get removed from the transcribed text. |
| "use_textbox" | true, false | true | If you want to send your text to VRChats Textbox. |
| "use_kat" | true, false | true | If you want to send your text to [KillFrenzyAvatarText](https://github.com/killfrenzy96/KillFrenzyAvatarText). |
| "use_both" | true, false | false | If you want to send your text to both options above, if both available and set to true. If not, the program will prefer sending to [KillFrenzyAvatarText](https://github.com/killfrenzy96/KillFrenzyAvatarText) if it is available. |
| "use_cpu" | true, false | false | Use CPU to transcribe, Always on if you downloaded the CPU version of this program. (Not editable on runtime) |
| "emotes" | - | - | All up to 80 emote slots and their corresponding phrase.

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
- Demo Gif/Video
- Implement Text To Speech

# Credit
- [OpenAI](https://github.com/openai) for their amazing work with anything really.
- [killfrenzy96](https://github.com/killfrenzy96) for [KillFrenzyAvatarText](https://github.com/killfrenzy96/KillFrenzyAvatarText) and [KatOSC](https://github.com/killfrenzy96/KatOscApp)
- [Frosty704's Billboard](https://github.com/Frosty704/Billboard) for making this project more useful.
