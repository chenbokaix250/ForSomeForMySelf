# os_cpu.h的解析


定位到源码地址:
`uC-OS2/Ports/ARM-Cortex-M/ARMv6-M/ARM/os_cpu.h`



1. 全局变量

OS_CPU_GLOBALS 和OS_CPU_EXT 允许我们是否使用全局变量。
```
#ifdef   OS_CPU_GLOBALS
#define  OS_CPU_EXT
#else
#define  OS_CPU_EXT  extern
#endif
```
若没有定义OS_CPU_GLOBALS，则以OS_CPU_EXT声明变量已经在外部定义。

2. 异常堆栈大小
```
#ifndef  OS_CPU_EXCEPT_STK_SIZE
#define  OS_CPU_EXCEPT_STK_SIZE    128u
#endif
```
默认的异常堆栈大小为128字节。

3. 数据类型
```
typedef unsigned char  BOOLEAN;
typedef unsigned char  INT8U;
typedef signed   char  INT8S;
typedef unsigned short INT16U;
typedef signed   short INT16S;
typedef unsigned int   INT32U;
typedef signed   int   INT32S;
typedef float          FP32;
typedef double         FP64;

typedef unsigned int   OS_STK;                   /* 堆栈的位宽为unsigned int，即32位 */
typedef unsigned int   OS_CPU_SR;                /* CPU状态寄存器的大小(PSR = 32位) */
```

4. 临界区保护

```
#define  OS_CRITICAL_METHOD   3

#if OS_CRITICAL_METHOD == 3
#define  OS_ENTER_CRITICAL()  {cpu_sr = OS_CPU_SR_Save();}
#define  OS_EXIT_CRITICAL()   {OS_CPU_SR_Restore(cpu_sr);}
#endif
```

当有异步事件发生时会引发中断请求，但CPU只有在中断开放其间才能响应中断请求。也就是说，所有的CPU都具有开/关中断指令，以便使一些代码不被中断的干扰。在uCOS-II中，那些不希望被中断的代码段就叫做临界区。

由于各厂商生产的CPU和c编译器的开/关中断的方法指令不尽相同，为增强os的可移植性，uCOS-II采用OS_ENTER_CRITICAL()和OS_EXIT_CRITICAL()两个宏封装了与系统硬件相关的开/关中断指令。

保护临界区有3种实现模式：
(1) OS_CRITICAL_METHOD = 1，表直接使用处理器的开/中断指令来实现宏

(2) OS_CRITICAL_METHOD = 2，这种模式可使CPU中断允许标志的状态在临界区前后不发生改变，在OS_ENTER_CRITICAL()中把CPU的允许中断标志保存在堆栈中，然后关闭中断，临界区结束时在调用OS_EXIT_CRITICAL()将保存在堆栈的中断状态恢复

(3) OS_CRITICAL_METHOD = 3，类似于模式(2)，但是用获得程序状态字的值，保存到变量中，而没有压到堆栈由源码可看出OS_CRITICAL_METHOD被define为3，所以使用的是模式3的方法保护临界区

5. 栈的类型及函数声明
OS_STK_GROWTH为1表是ARM的降栈，OS_TASK_SW()宏定义OSCtxSw()函数，该函数是用于操作系统任务切换的：
```
#define  OS_STK_GROWTH 1                 
#define  OS_TASK_SW()  OSCtxSw()
```
定义了两个全局数组用于堆栈，OS_CPU_ExceptStkBase为主堆栈，OS_CPU_ExceptStk为非主堆栈：
```
OS_CPU_EXT  OS_STK   OS_CPU_ExceptStk[OS_CPU_EXCEPT_STK_SIZE];
OS_CPU_EXT  OS_STK  *OS_CPU_ExceptStkBase;
```
声明开/关中断的函数原型：
```
#if OS_CRITICAL_METHOD == 3u                      /* See OS_CPU_A.ASM  */
OS_CPU_SR  OS_CPU_SR_Save(void);
void       OS_CPU_SR_Restore(OS_CPU_SR cpu_sr);
#endif
```
用于任务切换函数原型声明：
```
void       OSCtxSw(void);
void       OSIntCtxSw(void);
void       OSStartHighRdy(void);
void       OS_CPU_PendSVHandler(void);
```
为os提供systick定时器服务的函数原型声明：
```
/* See OS_CPU_C.C */
void       OS_CPU_SysTickHandler(void);
void       OS_CPU_SysTickInit(INT32U  cnts);
```

---

os_cpu.h中 主要定义了操作系统与硬件交互的声明.