# Adapter AUTOSAR初步II

Adaptive Autosar并不是为了取代Classic Autosar和非Autosar架构的平台，而是为了更好的与当前这些架构平台相互兼容、协作并满足未来的需求。例如Classic Autosar已增加对车载以太网SOME/IP的支持，而这对于Adaptive Autosar来说必须是基本操作，而且还会支持更加先进的通讯方式。

![层级结构](https://tva1.sinaimg.cn/large/008i3skNly1gy0vtqed8ij30bw0fi3zi.jpg)

## Adaptive Autosar的特点

### 1 以C++为实现形式

Adaptive Autosar平台的Applications都将采用C++编程，我们知道C是嵌入式系统的主要编程语言，具有执行速度快、效率高的特点；但在性能要求非常高的复杂应用和算法开发上（如机器学习、图像特征识别等）具有面向对象特性的C++显然比C更具有优势，而AP主要适应未来智能化和网联化的需求，这些需求的实现主要涉及复杂应用和复杂算法的开发，因此选用一种面向对象的编程语言是必要的。最新Release的Adaptive Autosar标准完全采用C++ 11/14作为首选语言。

![c++](https://tva1.sinaimg.cn/large/008i3skNly1gy0vuztvu4j30fo06et9b.jpg)

### 2 面向服务的通讯方式（SOA）

为了支持复杂的应用程序，并在并行处理和计算资源分配上具有最大的灵活性和可扩展性，AP采用面向服务的通讯架构。SOA主要基于以下概念：系统由一组服务构成，其中一个可使用另外一个的服务，应用程序Applications可根据自己的需要使用一个或多个服务；此外服务可以在应用程序运行的本地ECU上，也可在运行另一个AP实例的远程ECU上。

![SOA](https://tva1.sinaimg.cn/large/008i3skNly1gy0vwwjt39j30em0fv0t9.jpg)

### 3 并行处理能力

分布式计算本质上是并行的，先进的多核异构处理器既具有强大的计算能力也能为并行计算提供技术支持，随着多核异构计算技术的发展，AP具有扩展其功能和性能架构的能力。事实上，硬件和接口规范仅是实现AP的一部分，在OS等技术和开发工具的发展上对实现AP的应用也至关重要。

![并行处理](https://tva1.sinaimg.cn/large/008i3skNly1gy0vymgjo6j30nv09qab1.jpg)

### 4 利用现有标准

闭门重新造车是没有意义的，尤其在规范方面。正如C++中所描述的那样，AP采用重用和调整现有开放标准的策略，来促进AP本身更快的发展应用并在现有标准的生态系统中受益。因而开发的AP规范并不是随意引入新的标准，因为现有标准已提供了所需的功能需求。

### 5 具有一定的安全性

AP目标系统通常需要一定的安全性，新技术的引入不应破坏这些要求，尽管实现起来并非易事。为了应对该挑战，AP则将架构、功能和过程方法结合起来来保证一定的安全目标。AP架构是基于SOA的分布式计算架构，这种方式可保证功能组件更加独立而不受意外干扰，从而可实现专用功能的安全性，此外诸如C++编码指南等指导书有助于我们更加安全可靠的使用诸如C++的复杂编程语言。

![安全性](https://tva1.sinaimg.cn/large/008i3skNly1gy0vzv1aw2j30rj0e0wga.jpg)

### 6 动态部署

AP支持应用程序的动态部署，通过资源和通讯的动态管理来降低软件开发和集成的effort，从而实现短迭代周期。增量部署还支持软件开发阶段，就如开发个Beta版本的软件部署在控制器上去不断测试验证和修复，从而达到最终的正式版。

在AP架构下，不同的Applications可能由不同供应商提供，因此在产品交付阶段，AP允许系统集成商合理限制这种动态部署的特性以降低不必要的风险和影响。应用程序将受到Application Manifest中所规定的约束限制，几个应用程序的Manifest在设计时可能会产生相互影响，但在执行时，在配置的范围内，资源和通讯路径的动态分配仅可以限定的方式进行。

## Adaptive Autosar软件分层架构

下面是AP的软件分层架构，楼主随意选两点谈谈，谬误之处，还请指正。

![分层架构](https://tva1.sinaimg.cn/large/008i3skNly1gy0w26ad4rj30os0bhgn2.jpg)

在AP架构下，一切都是OS中的进程，这跟CP架构有着显著的区别，在CP架构下，所有应用都是静态配置的，即应用的进程在OS中被写死，一旦软件编译完成就不可更改，其调用的周期也是确定，因此基于CP架构的软件一旦有小的应用变更就得重新配置和编译：费时费力。而AP架构的软件就如计算机的工作原理，应用是动态运行的，何时调用、进程生存周期、资源占用及进程结束等都由系统动态管理，好比你手机上的App何时打开、运行后其会调用的资源及何时关闭都是动态进行的。

![多进程](https://tva1.sinaimg.cn/large/008i3skNly1gy0w36cq64j30mg0bemyl.jpg)

AP架构的优势能使车载控制器可如同手机一样（理想的目标），使应用实现动态的部署和升级更新。

![动态性](https://tva1.sinaimg.cn/large/008i3skNly1gy0w47b5mqj30a905nmx9.jpg)

在AP架构下每个Application都是一个App，每个App主要包含如下这些部分：

![application](https://tva1.sinaimg.cn/large/008i3skNly1gy0w5qg35uj30d30c80te.jpg)

![平台](https://tva1.sinaimg.cn/large/008i3skNly1gy0w6duaakj30cp08kmxv.jpg)

App都有一个非常重要的API->ara::com，这个API在分层架构下的位置如下：

![ara：com](https://tva1.sinaimg.cn/large/008i3skNly1gy0w72dxoaj30pb0azgnt.jpg)

ara::com使基于SOA的通讯方式成为可能，负责进程间和不同控制器间基于服务的通讯。

![通信](https://tva1.sinaimg.cn/large/008i3skNly1gy0w87y58hj30q00b6q48.jpg)

在AP这种灵活的框架下，ara::com可支持或扩展对车载以太网SOME/IP 、 TSN 、 DDS等SOA通讯技术的应用。

![扩展性](https://tva1.sinaimg.cn/large/008i3skNly1gy0w9tm3wij30qy0b6js4.jpg)

对Data Distribution Service（DDS）或基于时间敏感网络（TSN)等通讯技术的支持如下：

![支持性](https://www.suncve.com/wp-content/uploads/2020/10/Pasted-into-%E4%B8%80%E6%96%87%E7%9C%8B%E6%87%82%EF%BC%8CAdaptive-AUTOSAR%E4%BB%8E%E5%85%A5%E9%97%A8%E5%88%B0%E7%B2%BE%E9%80%9A%EF%BC%88%E4%BA%8C%EF%BC%89-14.png)![dds支持性](https://tva1.sinaimg.cn/large/008i3skNly1gy0wdoo0b2j30if09omy6.jpg)

## Adaptive Autosar的应用

Adaptive Autosar的应用是灵活的，下面楼主就列举三个吧。

### 1 大众MEB平台软件架构

我们知道针对互联化、智能化的趋势，大众推出MEB平台，期望从MQB分布式的E/E架构向MEB的中央集成式E/E架构过渡，并希望在后续的电动车上都采用最先进的MEB平台打造，构建从高端到平价的车辆体系，有点后发先至的感觉。

![大众](https://tva1.sinaimg.cn/large/008i3skNly1gy0wig5d2uj30n70dqtac.jpg)

大众带来了各系列车型的混动或纯电动版本，借助MEB平台，大众希望打造互联、智能并可具有高度扩展性、灵活性的整车系统。

![大众架构](https://tva1.sinaimg.cn/large/008i3skNly1gy0wkdsnp1j30nw08odgx.jpg)

而整车的软件架构毫无疑问需要AP架构的加入和支持，如下：

![ICAS架构](https://tva1.sinaimg.cn/large/008i3skNly1gy0wlixj7mj30o60e3ac5.jpg)

### 2 域控制器

域控制器也是最近这些年才热起来的，所谓的域就是将整车E/E架构划归为不同的区，如动力域、车身域、底盘域、娱乐域等，每个域只需要挂载单个控制器来负责所在域的通讯和控制，减少之前一个功能、一个“盒子”的分布式E/E架构复杂的布线和集成：其实就是将多个控制器的软件糅合进一个控制器。我们知道不同的控制器软件可能由一个或多个供应商提供，若由多个供应商提供，每个供应商除了负责各自软件的升级，还涉及复杂且不同类型软件的集成，那么显然AP架构可很好的满足这种需求，使不同的软件在单个多核控制器上的集成和升级工作变的相对容易些。

![域控制器](https://tva1.sinaimg.cn/large/008i3skNly1gy0wn49wzlj30ox0c8jsz.jpg)

### 3 自动驾驶应用

自动驾驶领域的竞争目前是十分火热的，既有传统大佬，也有新入玩家，目前主要的玩家有如下这些，但就如几年之前的手机操作系统一样，相信最终只有少数玩家才能赢得这场竞赛。

![自动驾驶厂家](https://tva1.sinaimg.cn/large/008i3skNly1gy0wnqm3o1j30s10b2jsn.jpg)

自动驾驶应用的加入使整车功能更加复杂，不同的应用可能由很多供应商提供，其次应用也越来越复杂，对计算资源和性能要求越来越高，需要更牛逼的硬件来支持，而AP架构既能满足应用对高性能计算的需求又具有一定的功能安全等级。

![等级划分与细节](https://tva1.sinaimg.cn/large/008i3skNly1gy0wonfqomj30qq0cxq4i.jpg)![自动驾驶关键技术](https://tva1.sinaimg.cn/large/008i3skNly1gy0wpbo0k4j30ke0aymym.jpg)

例如BMW计划在以后的自动驾驶系统方面，对软件组件进行重新设计，以支持不同的API要求，从而将软件合理布置在不同架构上发挥更优的功能。

![宝马布局](https://tva1.sinaimg.cn/large/008i3skNly1gy0wtx29sjj30q308tmyg.jpg)

## 总结

此次楼主又唠叨了很多，总体来说呢，CP架构虽然搞了这么多年但依然在路上，因为其依然需要不断的完善，由于CP标准的复杂性，到目前我们还没玩转，整车控制系统的软件架构要实现完美的Classic Autosar依然任重而道远；而AP架构伴随着互联化、网联化的趋势在这两年应运而生，其更需要不断的完善和发展。CP和AP不是为了谁取代谁，而是针对不同的应用领域和不同的功能安全要求相辅相成。