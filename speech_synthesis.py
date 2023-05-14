import os
import azure.cognitiveservices.speech as speechsdk
import configparser
import xml.etree.ElementTree as ET

config = configparser.ConfigParser()
config.read('config.ini')

speech_key = config.get('SPEECH', 'SPEECH_KEY')
speech_region = config.get('SPEECH', 'SPEECH_REGION')

file_name = config.get('OUTPUT', 'FILE_NAME')
file_path = config.get('OUTPUT', 'FILE_PATH')

speech_config = speechsdk.SpeechConfig(speech_key,speech_region)

# zh-CN-liaoning	中文（东北官话，简体）	
# zh-CN-liaoning-XiaobeiNeural 1，2（女）

# 说话的声音语言。
# Set either the `SpeechSynthesisVoiceName` or `SpeechSynthesisLanguage`.
speech_config.speech_synthesis_language = "zh-CN" 
speech_config.speech_synthesis_voice_name='zh-CN-liaoning-XiaobeiNeural'

directory = "./wav"

# 循环目录中的文件，并删除所有.wav文件
for filename in os.listdir(directory):
    if filename.endswith(".wav"):
        os.remove(os.path.join(directory, filename))

print("清除./wav目录下所有文件 Done!")

print("输入您想要解析文件还是字幕文本[f:文件,s:字幕(默认是s)] >")
type = input()

print("输入您是否用语音合成标记语言 (SSML)来转换[n:否,y:是(默认是y)] >")
api_type = input()

results = []
if type.lower()=='f':
    with open('temp.txt', 'r', encoding='utf-8') as file:
        text = file.read()

    print(text)
    results.append(text)
else:
    with open('subtitle.srt', 'r', encoding='utf-8') as file:
        lines = file.readlines()

    index = -1
    for i, line in enumerate(lines):
        line = line.strip()
        # 如果这一行是数字，则下一行必然是字幕内容
        if line.isdigit():
            index = i + 1
        # 如果这一行是空行，并且上一行是数字，则表示当前字幕块结束
        elif not line and index != -1:
            results.append(lines[index + 1].strip())
            index = -1

    print(results)

def speak_ssml_async(filename, text):
    # 定义命名空间URI和前缀
    ns = {
        'speak': 'http://www.w3.org/2001/10/synthesis',
        'mstts': 'https://www.w3.org/2001/mstts'
    }
    for prefix, uri in ns.items():
        ET.register_namespace(prefix, uri)
    # 加载XML文件
    tree = ET.parse('ssml.xml')
    # 获取<speak>节点
    root = tree.getroot()
    # 获取<mstts:express-as>节点
    express_as = root.find('.//mstts:express-as', ns)
    # 获取文本内容，替换为新文本
    express_as.text = text
    # 将修改后的XML写入文件
    tree.write('ssml.xml', encoding='utf-8')

    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)
    ssml_string = open("ssml.xml", "r").read()
    print(ssml_string)
    result = speech_synthesizer.speak_ssml_async(ssml_string).get()
    stream = speechsdk.AudioDataStream(result)
    stream.save_to_wav_file(filename)

def speak_text_async(filename, text):
    audio_config = speechsdk.audio.AudioOutputConfig(filename=filename)
    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
    speech_synthesis_result = speech_synthesizer.speak_text_async(text).get()

    if speech_synthesis_result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print("文本合成语音 [{}]".format(text))
    elif speech_synthesis_result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = speech_synthesis_result.cancellation_details
        print("语音合成已取消：{}".format(cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            if cancellation_details.error_details:
                print("错误详情：{}".format(cancellation_details.error_details))
                print("你设置了语音资源密钥和区域值吗？")

for i, text in enumerate(results):
    if type.lower()=="f":
        filename = file_name
    else:
        filename = file_path + str(i) + "_" + text + ".wav"
    if api_type.lower()=='n':
        speak_text_async(filename, text)
    else:
        speak_ssml_async(filename, text)
