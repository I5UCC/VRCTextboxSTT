# VRCTextboxSTT
A SpeechToText application that uses [OpenAI's whisper](https://github.com/openai/whisper) to transcribe audio and send that information to VRChats textbox system over OSC.

To make the program listen, you either have to press the button that is configured in the ***config.json*** file. ***` by default*** <br>
In VR, press the Left Controllers ***A Button*** for **Valve Index**, and the ***X-Button*** on **Oculus/Meta** respectively.

First startup will take longer, as it will download the configured language model. After that it will start up faster. <br>
More to that under [#Configuration](https://github.com/I5UCC/VRCTextboxSTT#configuration)

# Demo

[soon TM]

# Configuration
Configuration of this program is located in the ***config.json*** file:

| Option | Values | Default | Explanation |
|:------:|:------:|:-------:|:-----------:|
| "IP" | Any IP-Adress | "127.0.0.1" | IP to send the OSC information to. |
| "Port" | Any Port | 9000 | Port to send the OSC information to. |
| "model" | "tiny", "base", "small", "medium", "large" | base | What model of whisper to use. I'd recommend not going over "base". |
| "language" | "english", "german", "spanish", "" | english | Language to use, "english" will be faster then other languages. Leaving it empty "", will let the program decide what language you are speaking. |
| "dynamic_energy_threshold" | true, false | false | With dynamic_energy_threshold set to 'True', the program will continuously try to re-adjust the energy threshold to match the environment based on the ambient noise level at that time. I'd recommend setting the 'energy_threshold' value high when enabling this setting. |
| "energy_threshold" | 0-3500 | 100 | Under 'ideal' conditions (such as in a quiet room), values between 0 and 100 are considered silent or ambient, and values 300 to about 3500 are considered speech. |
| "pause_threshold" | 0.0-10.0 | 0.8 | Amount of seconds to wait when current energy is under the 'energy_threshold' |
| "keyboard_hotkey" | Any key supported by the [python keyboard library](https://github.com/boppreh/keyboard) | ` | The key that is used to trigger Listening. |
