## 模块argparse是Python标准库中推荐的命令行解析模块


#### 基础
```
import argparse
 
parser = argparse.ArgumentParser()
parser.parse_args()
```
运行上述脚本并且没有添加任何参数时，输出无结果

添加--help参数时，argparse模块会自动输出帮助信息，这是它的优势（参数--help也可以简化为-h，这两个参数是不需要我们编辑的）

当指定其他参数时报错，即便如此，也可以得到一个有用的用法信息

---
#### 位置参数
指定位置参数后,程序必须输入该参数值才能运行

```

import argparse
 
parser = argparse.ArgumentParser()
parser.add_argument("echo")
args = parser.parse_args()
print args.echo
```
增加add_argument()方法,在这个方法中,我们制定程序将要去接受的命令行选项,在这里我们命名位echo
此时,调用程序需要输入一个参数
方法parse_args()实际上会返回一些选项指定的值
在argparse模块中,当你指定位置参数名为echo时,此时想要提取该参数值,必须指定为args.echo
