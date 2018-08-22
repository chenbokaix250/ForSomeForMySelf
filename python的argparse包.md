## 模块argparse是Python标准库中推荐的命令行解析模块

```
import argparse
 
parser = argparse.ArgumentParser()
parser.parse_args()
```
运行上述脚本并且没有添加任何参数时，输出无结果

添加--help参数时，argparse模块会自动输出帮助信息，这是它的优势（参数--help也可以简化为-h，这两个参数是不需要我们编辑的）

当指定其他参数时报错，即便如此，也可以得到一个有用的用法信息

