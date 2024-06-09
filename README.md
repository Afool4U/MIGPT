# MIGPT
 基于API流式对话的低延迟版MIGPT
 
## 简单介绍
本项目利用了OpenAI官方API的原生流式传输对话方式，无需等待，即刻对话！

在作者的笔记本上，实测从提问到回答的时间仅不到1.5秒（当然，这个时间也取决于你的梯子和网络质量）。
 
_* 点[此链接](https://v.douyin.com/Sg8rMrJ/)观看2分半的测试视频_
 
![image](https://github.com/Afool4U/MIGPT/blob/main/%E6%95%88%E6%9E%9C.png)

_注意：本项目因采用了流式传输，暂时不支持LX04、L05B和L05C型号。如您的音箱是该型号，请使用[xiaogpt](https://github.com/yihong0618/xiaogpt)。_

## 详细介绍
### 项目描述

本项目旨在通过集成ChatGPT与小爱同学，打造一个创新的智能家居控制方案。该方案通过高效的API调用与流式对话技术，实现了快速、自然的家居设备控制和交互。核心功能包括使用OpenAI官方API进行流式对话传输，设备状态实时监控与控制，基于微调BERT +动态量化和TF-IDF特征+SVM的大模型自动调用功能（_此功能还未上传，需要可以加QQ交流群：622695590_）。

### 主要工作

集成ChatGPT与小爱同学：通过高效的API调用，实现了与ChatGPT的无缝连接，为用户提供即时、准确的对话交互体验。利用小爱同学的设备控制能力，扩展了智能家居的交互方式。
流式对话处理：引入基于生产者-消费者模式的流式对话技术，创新性地使用了流式对话的分割算法，无需等待完整回复即可相应，相对其他项目平均减少80%的用户等待时间，大大而提高了交互效率和用户满意度。
自研大模型调用算法：创新性的使用深度学习和机器学习技术，从用户被动手动开关模型到自动调用大模型，既引入了大模型的智慧能力，又不影响家居控制、天气查询等操作，实现了真正意义上的无缝接入。 项目提供两个可选择模型：基于微调BERT +8位动态量化的大模型分类器，基于TF-IDF特征+SVM的分类器。通过自己收集的数据集训练，准确率均能达到90%以上。
用户体验优化：在项目设计中注重用户体验，采用异步编程模型处理并发请求，通过动态的交互提示和及时的反馈，提升了用户使用的舒适度和满意度。

### 项目特点

实时性与效率平衡：在保证对话实时性的同时，优化算法以减少处理延时，是本项目的一个技术特点。通过流式对话分割算法有效解决了这一问题，实现了快速响应。
大模型调用算法：传统接入方案无法同时使用原生小爱模型和GPT模型，两者只能取其一，无法做到长期实际部署。通过使用NLP技术，使用自行收集的数据集，分别训练了深度和机器学习模型，从用户被动手动开关模型到自动调用大模型，既引入了大模型的智慧能力，又不影响家居控制、天气查询等操作，实现了真正意义上的无缝接入。

## 使用方法
_分为3个steps:_

### step 1 :

  在项目路径执行pip install -r requirements.txt安装需要的依赖。
  如果没有C++编译环境，则安装tiktoken时会报如下错误：distutils.errors.DistutilsPlatformError: Microsoft Visual C++ 14.0 or greater is required. Get it with "Microsoft C++    Build Tools"）。

  解决方法:

  (1) 本地执行pip debug --verbose查看当前平台支持的版本，然后在[此链接](https://pypi.tuna.tsinghua.edu.cn/simple/tiktoken/)中找到对应版本的whl文件并下载。

  (2) 在whl文件同级目录执行pip install "whl全名带后缀"，注意：不要修改原始whl文件的名称。
  
### step 2 :
  在[MIGPT.py](https://github.com/Afool4U/MIGPT/blob/main/MIGPT.py)中填写小米账号、密码、[API Key](https://platform.openai.com/account/api-keys)和音箱型号。
  
### step 3 :
  科学上网后，运行[MIGPT.py](https://github.com/Afool4U/MIGPT/blob/main/MIGPT.py)文件即可。
  
## 使用技巧

1. 运行过程中，可用“打开/关闭高级对话"控制是否打开ChatGPT。
2. 当ChatGPT正在回答问题时，可用“闭嘴”或“停止”终止回答。
3. 可随时提问新的问题打断ChatGPT的回答。

## 致谢引用

- @[yihong0618](https://github.com/yihong0618) 的 [xiaogpt](https://github.com/yihong0618/xiaogpt) 
- @[acheong08](https://github.com/acheong08) 的 [ChatGPT](https://github.com/acheong08/ChatGPT)
- @[Yonsm](https://github.com/Yonsm) 的 [MiService](https://github.com/Yonsm/MiService) 

## 联系作者

请联系QQ : 2312163474
