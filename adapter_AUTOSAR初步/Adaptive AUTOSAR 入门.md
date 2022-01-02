# Adaptive AUTOSAR 入门



![汽车发展趋势](https://tva1.sinaimg.cn/large/008i3skNly1gxztldxokhj30nx0bl407.jpg)

智能化、网联化和电动化是汽车未来的发展趋势，而正是这样的变化，将会给汽车E/E架构和软件架构带来巨大的革新，在以前哪怕现在，汽车仍主要作为一个代步工具以满足我们的出行需求，而与我们的信息娱乐生活所分离，在未来汽车将与我们的日常生活息息相关。

![架构革新](https://tva1.sinaimg.cn/large/008i3skNly1gxztmcgw8oj30mu0bvq43.jpg)

## 新四化对汽车软件架构的革新

1、汽车智能化的实现需要大量数据的实时处理以用于计算机视觉或基于多传感器输入的模型推导，应用程序通过对数据的并行处理及时给出解决方案，高性能计算首先需要新硬件架构的支持，例如异构多核处理器、GPU加速等；其次也需要依赖新的软件架构以支持跨平台的计算处理能力、高性能微控制器的计算以及分布式和远程诊断等。

![autosar](https://tva1.sinaimg.cn/large/008i3skNly1gxzto6xtm4j30ie074mxw.jpg)

2、Car-2-X应用的实现需要车辆与车外系统的互动，而这会涉及动态通讯及大量数据的有效分配，例如对于交通路况的及时获取还需要第三方合作伙伴的参与，因此新软件架构还需支持云交互以及非Autosar系统的集成。

![Car-2-x](https://tva1.sinaimg.cn/large/008i3skNly1gxztpgy92hj30tx0angnn.jpg)

3、车辆在云端的互连需要专用安全手段的支持，以确保云交互和车载系统的通讯安全。

![云端支持](https://tva1.sinaimg.cn/large/008i3skNly1gxztqqd871j30si0a3dhm.jpg)

4、新四化的趋势将需要汽车软件系统的更强互动，汽车软件既要安全又可更新以反映新的功能特性或法规要求，这就需要新架构支持软件组件的动态部署以及非Autosar架构与非车载系统之间的交互。

![更强互动](https://tva1.sinaimg.cn/large/008i3skNly1gxztrp0fydj30lj083t9l.jpg)

## 新四化对E/E架构的革新

当前汽车E/E架构一直遵循着“一个功能一个盒子”的分布式架构模式，在这样的汽车电子电气架构形式下，每增加一个功能，就需要增加相应的控制器和通讯信号，进一步增加系统的复杂性，如下两点因素将重塑未来E/E架构。

### 1、异构软件平台的系统集成

今天的汽车E/E架构虽可分别划归到信息娱乐、底盘和动力总成等不同域中，但信息娱乐系统通常使用Linux或商业化的通用操作系统，Autosar经典平台则是实时性很强的嵌入式ECU标准，随着未来新技术及深度嵌入式系统对计算能力不断增长的需求，急需第三种控制控制器-域控制器用于集成特定领域的功能特性（如车辆运动域、车身域等），形成域集中或跨域集中式电子电气架构。

![异构平台](https://tva1.sinaimg.cn/large/008i3skNly1gxztv34n3qj30i809dwfs.jpg)

### 2、由基于信号向面向服务（SOA）的通讯方式转变

传统汽车通讯仍是基于信号的通讯方式，即信息发送者不Care谁接收而只负责将信号发送出去，接收者也不Care是谁发送的而只负责接收自己的想要的即可，这种方式非常适用于有限大小控制数据的应用场景。而诸如自动驾驶等先进应用场景加入后，大量数据的动态交互必须采用面向服务的通讯方式以提高通讯效率降低负载，在该种方式下，接收者作为客户端，只需要查找、订阅服务等待接收信息即可，而发送者作为服务提供者只需要给订阅者提供服务和信息即可。基于信号和面向服务的两种通讯方式的结合对未来的E/E架构提出例如严峻的挑战。

![SOA](https://tva1.sinaimg.cn/large/008i3skNly1gxztw9am1mj30it0a3myk.jpg)

在未来，随着汽车电子及软件功能的大幅增长，最终可能向基于中央计算机的车辆集中式电子电气架构，甚至车-云协同控制发展。

![车云协同](https://tva1.sinaimg.cn/large/008i3skNly1gxztwv8zgmj30lv0a2myi.jpg)

在这样的趋势下，需要一高度灵活、高性能且支持HPC、动态通讯等特性的新软件架构平台---Adaptive Autosar。

![Adaptive AUTOSAR](https://tva1.sinaimg.cn/large/008i3skNly1gxzty4ar6gj30qg0e4tb9.jpg)

### Classic Autosar与Adaptive Autosar的比较

当前汽车控制器，如ECU与其他功能或信息娱乐性控制器有明显的不同，基于Autosar经典平台开发的汽车控制器，具有如下特点：

1、硬实时，可在us时间内完成事件的实时处理，硬实时任务必须满足最后期限的限制，以保证系统的可靠运行。

2、高功能安全等级，其可达到ASIL-D的安全等级。

3、对CPU、RAM或Flash等资源具有较低的占用率。

4、软件功能通常是固化不可动态变更的。

而信息娱乐性控制器，则正好与上相反，其一般会占用较大的硬件资源，且一般不具有实时性，因其一般运行在嵌入式PC上，如LINUX，而不是汽车级操作系统上，所以其即使出现故障也不会造成严重的安全事故。而Apdative Autosar则是连接这两者的桥梁，其具有如下特点：

1、软实时，具有毫秒级内的最后期限，且偶尔错过最后期限也不会造成灾难性后果。

2、具有一定的功能安全要求，可达到ASIL-B或更高。

3、与经典平台不同的是，它更适用于多核动态操作系统的高资源环境，如QNX。

![cp和ap区别](https://tva1.sinaimg.cn/large/008i3skNly1gxztzz8erlj30j80avwfu.jpg)

Adaptive Autosar与Classic Autosar相比，虽实时性要求有所降低，但在保证一定功能安全等级的基础上，大大提高了对高性能处理能力的支持，以支持智能互联应用功能的开发，因此C++将成为Adaptive Autosar平台的主要开发语言。

![cp与AP对比2](https://tva1.sinaimg.cn/large/008i3skNly1gxzu0z77gmj30qi0ctq4w.jpg)

### Adaptive Autosar架构

Adaptive Autosar架构如下：主要包括硬件/虚拟机层、基础层、服务层和应用层。

![AP架构](https://tva1.sinaimg.cn/large/008i3skNly1gxzu1xg7tkj30gx08kjs5.jpg)

![架构2](https://tva1.sinaimg.cn/large/008i3skNly1gxzu2ecaadj30qf0ba412.jpg)

Adaptive Application是多进程且可处于不同的执行状态，Manifest是arxml类型的文件，其主要包含平台相关的信息，例如恢复操作以及与服务或库相关的依赖关系（说实话到这我都感觉基本是ROS的架构了），Adaptive Autosar基础模块在布置和更新应用时会读取该文件，Instance 配置文件主要包含静态的信息，如版本信息等。

![Adaptive Application](https://tva1.sinaimg.cn/large/008i3skNly1gxzu3tbqjrj30dx0anq3j.jpg)

### 1、ara::com---通讯管理接口

其可实现应用之间的函数调用和事件发送
服务请求：双向数据流，即发送请求者会收到服务端的反馈，可支持多对1的服务请求，即单个服务可被不同客户端调用，客户端可串行或并行进行反馈，具体流程如下：

![服务请求](https://tva1.sinaimg.cn/large/008i3skNly1gxzudmi0q3j30qd08fwfe.jpg)

事件发送：由客户端发起，单向数据流。即数据只可从服务端向客户端流动，支持单个服务向多个客户端的事件发送，流程如下：

![时间发送](https://tva1.sinaimg.cn/large/008i3skNly1gxzugl2akij30qd07tgmd.jpg)

### 2、ara::em---执行管理

控制器启动阶段：主要进行OS的启动，检查安装的应用，如扫描应用的manifest文件，并负责应用的启动（fork(),exec()）。

控制器运行阶段：使应用运行在状态机所期望的状态，并监测状态机状态的改变和进程的终止。

![执行管理](https://tva1.sinaimg.cn/large/008i3skNly1gxzuhbacjgj30el0btdgg.jpg)

### 3、ara::diag---诊断管理

![诊断管理](https://tva1.sinaimg.cn/large/008i3skNly1gxzulkeigsj30el0btdgg.jpg)

### 4、ara::per---存储管理

其主要对非易失性存储器进行操作，实现流存储及对关键数据的存储。

![存储管理](https://tva1.sinaimg.cn/large/008i3skNly1gxzuoofcu8j307l0a53yu.jpg)

Adaptive Autosar的出现并不是为了取代Classic Autosar平台，而是针对不同的应用场景实现两者的共存和协作，Classic Autosar平台支持高安全性和高实时性的应用场景，因此对于深度嵌入式的软件功能需部署运行在经典平台上；而Adaptive Autosar则支持大数据的并行处理，所以对于高性能运算的功能则需要运行在Adaptive平台上。

![共存与协作）](https://tva1.sinaimg.cn/large/008i3skNly1gxzupxans6j30r90blmy7.jpg)

![系统整合](https://tva1.sinaimg.cn/large/008i3skNly1gxzuqp1hevj30n00bywg7.jpg)

备注：上图有没有看到ROS的熟悉身影

## 总结

随着无人驾驶技术的如火如荼，车联网及万物互连、云技术的日益发展，Adaptive Autosar的出现不仅可满足现有需求，还可满足未来汽车技术的革新变化，由于其支持各种自适应的部署、复杂的微控制器以及各种非Auosar系统的互动，未来汽车将拥有不同类型的架构并互相进行补充。