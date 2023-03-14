# MIGPT
 基于API流式对话的低延迟版MIGPT
 
## 简单介绍
本项目利用了OpenAI官方API的原生流式传输对话方式，无需等待，即刻对话！

在作者的笔记本上，实测从提问到回答的时间仅不到1.5秒（当然，这个时间也取决于你的梯子和网络质量）。
 
 
![image](https://github.com/Afool4U/MIGPT/blob/main/%E6%95%88%E6%9E%9C.png)


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
