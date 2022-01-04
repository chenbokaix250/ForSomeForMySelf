# μCOS-II源码下载及源码目录结构

功课RTOS之旅,扬帆起航!

μCOS-II的源码托管在github中
`https://github.com/weston-embedded/uC-OS2.git`

>μ的输入需要切换输入法,为提高效率,今后采用uCOS2代替.

## 源码目录结构如下:

* Cfg 用于与应用层配置对接
* Ports 用于与底层平台对接
* Source 源代码
* TLS 新特性(先不看)
* Trace 说明

Ports结构以ARM-Cortex-M/ARMv6-M为例:
* ARM 
* GNU
* IAR
给出了不同开发平台对应的底层文件:
* os_cpu.h
* os_cpu_a.asm
* os_cpu_c.c
* os_dbg.c
大致都包含这四个文件.

(1) os_cpu.h：定义数据类型、处理器相关代码、声明函数原型
(2) oc_cpu_a.asm：与处理器相关的汇编代码，主要是与任务切换相关
(3) os_cpu_c.c：定义用户钩子函数，提供扩充软件功能的的接口
(4) os_dbg.c：内核调试相关数据和相关函数

---

重点在**Source**文件夹中:
1. os_core.c:内核数据结构管理,ucos2的核心,涵盖内核的初始化,任务切换，事件块管理、事件标志组管理等功能.
2. os_dbg_r.c:内核调试相关的管理
3. os_flag.c:事件标志组
4. os_mbox.c:消息邮箱
5. os_mem.c:内存管理
6. os_mutex.c:互斥锁
7. os_q.c:队列
8. os_sem.c:信号量
9. os_task.c:任务管理
10. os_time.c:时间管理,主要实现延时
11. os_tmr.c:定时器管理,设置定时时间,超时则调用超时函数
12. os_trace.c:代码跟踪器的支持
13. os.h:正常情况下不会使用,作用是与ucos3兼容
14. ucos_ii.h:内部函数参数设置
15. ucos_ii.c:防止文件包含