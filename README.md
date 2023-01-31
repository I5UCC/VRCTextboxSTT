# VRCTextboxSTT [![Github All Releases](https://img.shields.io/github/downloads/i5ucc/VRCTextboxSTT/total.svg)](https://github.com/I5UCC/VRCTextboxSTT/releases/latest) <a href='https://ko-fi.com/i5ucc' target='_blank'><img height='35' style='border:0px;height:25px;' src='https://az743702.vo.msecnd.net/cdn/kofi3.png?v=0' border='0' alt='Buy Me a Coffee at ko-fi.com' />
### A SpeechToText application that uses [OpenAI's whisper](https://github.com/openai/whisper) to transcribe audio and send that information to VRChats textbox system and/or [KillFrenzyAvatarText](https://github.com/killfrenzy96/KillFrenzyAvatarText) over OSC.

### This program is supposed to be entirely free(as in money) and independent of Cloud Based Transcription services like Microsoft Azure etc., by using transcription Algorithms running on your own hardware, thus respecting privacy and improving latency and reliability, all to the cost of compromising a bit of performance for running on your hardware.

# [Download Here](https://github.com/I5UCC/VRCTextboxSTT/releases/latest)

# Demo

[soon TM]

# Requirements
With default settings, this program has following requirements:

- CPU version (Slower, Lower Requirements, Smaller Performance Compromises): <br>
  - ~2GB of storage space <br>
  - ~1GB of available RAM<br>
- GPU version (Faster, Higher Requirements, Bigger Performance Compromises): <br>
  - CUDA enabled GPU (NVIDIA ONLY), otherwise it will fall back to using CPU <br>
  - ~5GB of storage space <br>
  - ~1GB of available RAM<br>
  - ~1GB of available VRAM<br>
- SteamVR (IF ran in VR, no Oculus support as of now.)

# Features
- Customizable button
  - You can bind the button to start transcription to any action that SteamVR allows you to set.
  - You can bind it to any key on your keyboard.
- Audio feedback for each step in the transcription.
- Multi Language support. whisper supports around [100 different languages](https://github.com/openai/whisper/blob/main/whisper/tokenizer.py#L10), with a few limitations.
- Sending transcription to either VRChats Ingame Textbox allowing for use with any avatar, or to [KillFrenzyAvatarText](https://github.com/killfrenzy96/KillFrenzyAvatarText) that needs to be integrated to an avatar. You can use [Frosty704's Billboard](https://github.com/Frosty704/Billboard) to add a speech bubble to your avatar.
- Free to use as of the [GPL-3.0 license](https://github.com/I5UCC/VRCTextboxSTT/blob/main/LICENSE)

# How to use
- Activate OSC in VRChat: <br/><br/>
![EnableOSC](https://user-images.githubusercontent.com/43730681/172059335-db3fd6f9-86ae-4f6a-9542-2a74f47ff826.gif)
- Run the program.
- The program will use your standard microphone set in windows.
- if you have a lot of background noise you should play around with the "energy_threshold" option in the ***config.json*** file to get it working well.
- Press A on the left Controller on index or X on Oculus or F1 on your Keyboard.
- Holding any of those for 1.5s clears the chatbox or cancels the action.

## OSC Troubleshoot

If you have problems with this program, try this to fix it:
- Close VRChat.
- Open 'Run' in Windows (Windows Key + R)
- Type in `%APPDATA%\..\LocalLow\VRChat\VRChat\OSC`
- Delete the folders that start with 'usr_*'.
- Startup VRChat again and it should work.

# Configuration
You can either Edit this configuration manually by editing the ***config.json*** file, or you can change those settings in the Program itself by clicking "Settings" in the bottom right.

| Option | Values | Default | Explanation |
|:------:|:------:|:-------:|:-----------:|
| "IP" | Any IP-Adress | "127.0.0.1" | IP to send the OSC information to. |
| "Port" | Any Port | 9000 | Port to send the OSC information to. |
| "osc_server_port" | Any Port | 9001 | Port to get the OSC information from. Used to improve KAT sync with in-game avatar and autodetect sync parameter count used for the avatar." |
| "model" | "tiny", "base", "small", "medium", "large" | base | What model of whisper to use. I'd recommend not going over "base" as it will significantly impact the performance |
| "language" | "english", "german", "spanish", "" | english | Language to use, "english" will be faster then other languages. Leaving it empty "", will let the program decide what language you are speaking. |
| "hotkey" | Any key supported by the [python keyboard library](https://github.com/boppreh/keyboard) | F1 | The key that is used to trigger listening. |
| "dynamic_energy_threshold" | true, false | false | With dynamic_energy_threshold set to 'True', the program will continuously try to re-adjust the energy threshold to match the environment based on the ambient noise level at that time. I'd recommend setting the 'energy_threshold' value high when enabling this setting. |
| "energy_threshold" | 0-3500 | 200 | Under 'ideal' conditions (such as in a quiet room), values between 0 and 100 are considered silent or ambient, and values 300 to about 3500 are considered speech. |
| "pause_threshold" | 0.0-10.0 | 0.8 | Amount of seconds to wait when current energy is under the 'energy_threshold' |
| "timeout_time" | 0.0-10.0 | 3.0 | Amount of time to wait for the user to speak before timeout |
| "hold_time" | 0.0-10.0 | 1.5 | amount of time to hold the button to clear the Textbox |
| "max_transcribe_time" | 0.0-20.0 | 0.0 | maximum amount of time for transcribing a message before transcribing gets cancelled. 0.0 is infinite |
| "microphone_index" | null, 0-10 | null | Index of the microphone to use. null is the System Default mircophone. |
| "banned_words" | ["word1", "word2", ...] | null | Array of banned words that are gonna get removed from the transcribed text. |
| "use_textbox" | true, false | true | If you want to send your text to VRChats Textbox. |
| "use_kat" | true, false | true | If you want to send your text to [KillFrenzyAvatarText](https://github.com/killfrenzy96/KillFrenzyAvatarText). |
| "use_both" | true, false | false | If you want to send your text to both options above, if both available and set to true. If not, the program will prefer sending to [KillFrenzyAvatarText](https://github.com/killfrenzy96/KillFrenzyAvatarText) if it is available. |
| "use_cpu" | true, false | false | Use CPU to transcribe, Always on if you downloaded the CPU version of this program. |

# Available models

There are five model sizes, four with English-only versions, offering speed and accuracy tradeoffs. Below are the names of the available models and their approximate memory requirements and relative speed. 


|  Size  | Parameters | English-only model | Multilingual model | Required VRAM | Relative speed |
|:------:|:----------:|:------------------:|:------------------:|:-------------:|:--------------:|
|  tiny  |    39 M    |     `tiny.en`      |       `tiny`       |     ~1 GB     |      ~32x      |
|  base  |    74 M    |     `base.en`      |       `base`       |     ~1 GB     |      ~16x      |
| small  |   244 M    |     `small.en`     |      `small`       |     ~2 GB     |      ~6x       |
| medium |   769 M    |    `medium.en`     |      `medium`      |     ~5 GB     |      ~2x       |
| large  |   1550 M   |        N/A         |      `large`       |    ~10 GB     |       1x       |

For English-only applications, the `.en` models tend to perform better, especially for the `tiny.en` and `base.en` models. OpenAI observed that the difference becomes less significant for the `small.en` and `medium.en` models.

# Modifying the bind for SteamVR
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
- Demo Gif/Video
- Implement Text To Speech

# Credit
- [OpenAI](https://github.com/openai) for their amazing work with anything really.
- [killfrenzy96](https://github.com/killfrenzy96) for [KillFrenzyAvatarText](https://github.com/killfrenzy96/KillFrenzyAvatarText) and [KatOSC](https://github.com/killfrenzy96/KatOscApp)
