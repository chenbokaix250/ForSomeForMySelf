# TensorFlow构件图

### 核心图数据结构
* tf.Graph 
>包含tf.Operation 
>graph must be launched in a session,then Operation can be executd! Exe by tf.Session.run op.run()
* tf.Operation 
>Operation连接输入和输出
* tf.Tensor
>tensor 用于输入在Operation之间传递
>graph launched in Session,Tensor can be computed by **tf.Session.run()**


### 张良类型
* tf.DType
* tf.as_dtype

### 实用功能
* tf.device
tf.device(device_name_or_function)
* tf.container
* tf.namescope
定义Python操作时实用的桑下文管理器
* tf.control_dependencies
* tf.convert_to_tensor
Converts the given value to a Tensor.
* tf.get_default_graph
default graph for thr current thread.
* tf.liad_file_system_library
加载tf插件,包含文件系统的实现
* tf.load_op_library(library_filename)
加载tf插件,包含传统的ops和kernels


## 生成常量,序列和随机值
### 生成常量
* tf.zeros //零
* tf.zeros_like
* tf.ones  //对角
* tf.noes_like
* tf.fill  //全
* tf.constant //固定值
---
* tf.lin_space
lin_space(
    start,
    stop,
    num,
    name=None
)
(stop - start)/num -1
均分计算指令,在间隔中生成值
* tf.range 
range(start, limit, delta=1, dtype=None, name='range')
创建一个数字序列，该数字开始于 start 并且将 delta 增量扩展到不包括 limit 的序列
像 Python 内置的 range，start 默认为 0，所以 range(n) = range(0, n)

* tf.random_normal
random_normal(
    shape,
    mean=0.0,
    stddev=1.0,
    dtype=tf.float32,
    seed=None,
    name=None
)
shape 一维整数张量或python数组.输出张量的形状.
mean dtype类型的 正态分布的均值
stddev 正态分布的标准差
dtype 输出的类型
seed 随机种子
name 操作的名称

* tf.bitwise 位操作模块
* tf.compat 


![TEST](https://ws1.sinaimg.cn/large/006tNc79ly1fvndrwd4vtj307705e0so.jpg)
