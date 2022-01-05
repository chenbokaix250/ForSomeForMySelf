# os_cpu_a.asm

代码地址:
`uC-OS2/Ports/ARM-Cortex-M/ARMv6-M/ARM/os_cpu_a.asm`
`.asm`文件说明 是汇编写成的
---

1. 声明外部变量和导出符号
```
EXTERN  OSRunning           ; External references
EXTERN  OSPrioCur
EXTERN  OSPrioHighRdy
EXTERN  OSTCBCur
EXTERN  OSTCBHighRdy
EXTERN  OSIntNesting
EXTERN  OSIntExit
EXTERN  OSTaskSwHook

EXPORT  OS_CPU_SR_Save      ; Functions declared in this file
EXPORT  OS_CPU_SR_Restore
EXPORT  OSStartHighRdy
EXPORT  OSCtxSw
EXPORT  OSIntCtxSw
EXPORT  OS_CPU_PendSVHandler
```
EXTERN声明的是变量，该变量来自外部(IMPORT声明的则是函数，表示该函数来自外部)。
EXPORT表示将该符号从本文件中导出，可供外部调用。

2. 内核异常相关寄存器地址定义
```
NVIC_INT_CTRL   EQU     0xE000ED04  ; 中断控制及状态寄存器ICSR的地址
NVIC_SYSPRI14   EQU     0xE000ED22  ; 系统异常优先级寄存器PRI_14
NVIC_PENDSV_PRI EQU           0xFF  ; 定义PendSV的优先级为255，即最低
NVIC_PENDSVSET  EQU     0x10000000  ; ICSR的位28，写1表悬起PendSV中断，读取它得到PendSV的状态
```

3. 堆栈分段对齐相关

```
AREA |.text|, CODE, READONLY, ALIGN=2   ; AREA |.text|表示选择段, CODE是代码段, READONLY表示只读, ALIGN=2表4字节对齐, 2^n对齐
THUMB                                   ; THUMB代码
REQUIRE8                                ; 指定当前文件要求堆栈八字节对齐
PRESERVE8                               ; 指定当前文件保持堆栈八字节对齐
```
4. 开关中断源函数实现
```OS_CPU_SR_Save
    MRS     R0, PRIMASK     ; 保存全局中断标志，将PRIMASK的值保存在R0(保存全局中断标志)
    CPSID   I               ; 关闭中断
    BX      LR              ; LR保存在函数调用前的地址，跳转回LR地址处，返回值保存在R0

OS_CPU_SR_Restore
    MSR     PRIMASK, R0     ; 读取R0的值设置PRIMASK(恢复全局中断标志)，通过R0传递参数
    BX      LR              ; LR保存在函数调用前的地址，跳转回LR地址处```

OS_CPU_SR_Save和OS_CPU_SR_Restore在前面的os_cpu.h文件中出现过：

```#define  OS_ENTER_CRITICAL()  {cpu_sr = OS_CPU_SR_Save();}
#define  OS_EXIT_CRITICAL()   {OS_CPU_SR_Restore(cpu_sr);}```

用于实现临界区的保护。

5. 任务的切换
任务切换是uCOS-II的核心之一。所谓的任务切换，是指从原来的任务中离开，转去执行新的任务。而切换的实现核心是：保存上下文，恢复将要去执行的任务的上下文件，跳转到新的任务中去执行。问题的关键在于，os不能够简单粗暴的跳转到新任务中去执行，所以Cortex-M3内核中PendSV机制来实现任务的切换。

要了解什么是PendSV，先要了解SVC。SVC和PendSV都属于内核异常，所以参考资料《Cortex-M3权威指南.pdf》。

SVC即系统服务调用，也称系统调用；PendSV为可悬起的系统调用，它们用于操作系统之上的软件开发中。

操作系统不可让用户程序(APP)直接操作硬件，所以当APP要访问硬件的时候，os会产生一个SVC异常，然后os提供的SVC异常服务程序得到执行，它再调用相关的操作系统函数，以完成APP的请求。

这样方式很方便灵活，具有的优点有：
(1) APP不用直接控制硬件，而是交由OS赋值具体的硬件操作，APP开发得到简化，编译APP的移植
(2) OS代码经过充分的测试，使得系统更加稳健可靠
(3) APP可以在无需特权级执行，APP不用担心误操作而时OS崩溃

SVC异常通过执行”SVC”指令产生，该指令需要一个立即数充当系统调用代号。SVC异常服务函数会根据此代号解释本次SVC调用的具体要求，再调用对应的服务函数：

`SVC 0x4  ;调用4号系统服务`

在学习ARM9裸板的时候，有一个软中断指令SWI，其实SVC的地位和SWI是相同的，其机器码也相同。然而在CM3内核中，因为异常处理模型已经更换，所以该指令也被重命名，以强调SVC是在新生的系统中使用的。

与之相关的异常是PendSV。SVC异常要求必须立即得到响应，若因优先级比当前正处理的中断服务函数低等原因使之无法立即得到响应，将造成硬FAULT。PendSV则不同，它可以像普通中断一样被悬挂起。OS可以利用PendSV的”缓期执行”机制去缓期执行一个异常，”缓”到什么时候？`当然是缓到当前重要的任务完成。

使用PendSV的方法是：手工往NVIC的PendSV悬起寄存器中写1，悬起后，若优先级不够高，则缓期执行。

假设系统中有两个就绪任务，正通过systick异常启动任务切换：

![2_systick.png](https://s2.loli.net/2022/01/06/cNJgyKt9qrBfQLW.png)


假设当前执行A任务，在A任务将呼叫SVC来请求切换到B任务的同时，发生一个中断要去执行对应的中断服务函数，那么OS该何去何从？
(1) 假设此时去执行任务切换，那么切换到B后将执行B任务的代码，中断服务函数将不知什么时候被执行
(2) 假设此时去执行中断服务函数，那么任务切换动作也不知道要什么时候得以执行

uCOS-II是一个实时操作系统，所谓”实时”就是及时响应系统中发生的任何异常，无论是(1)还是(2)都会使得系统非实时。因为是SVC机制，所以在CM3中，若os在某中断服务活跃的时候尝试切换任务将触发fault异常。在早期的OS中会检测当前是否有中断在活跃，在没有任务中断需要响应时才执行上下文切换，切换期间无法响应中断。这种方法的弊端在于，任务切换操作可能会拖延很久才得到执行(一直在响应IRQ，没时间顾得上任务切换)。

在引进PendSV机制后，问题得到解决：

![2_PendSV.png](https://s2.loli.net/2022/01/06/T653AkWMac9byJg.png)


任务切换时没遇到中断请求的场景：
(1) 任务A呼叫SVC来请求任务切换
(2) OS接收到SVC请求后，不立即进行任务切换，而只是做任务切换的准备，并且Pend一个PendSV异常
(3) 当CPU退出SVC服务函数后，立即进入PendSV服务函数，执行上下文切换
(4) PendSV服务函数执行完毕后，回到任务B

任务切换时遇到中断请求的场景：
(1) 发生了一个中断，CPU在执行该中断的中断服务函数(ISR)
(2) 在执行ISR的同时，发生systick异常，任务B呼叫SVC来请求任务切换
(3) CPU暂时放弃ISR继续执行，而是执行一些必要操作，在SVC服务函数中Pend一个PendSV异常
(4) CPU退出SVC服务函数后，回到ISR继续执行
(5) ISR执行完毕后PendSV服务函数得到执行，在函数中实现上下文切换
(6) 切换完毕，回到任务A

要实现这个任务切换机制，我们需要手动将PendSV设置为最低优先级的异常。为什么？

因为只有PendSV比当前正在响应的中断源，或者在切换任务的同时发生的中断的中断优先级低时，PendSV的中断服务才会被挂起。设置为最低优先级才保证PendSV中断服务能被悬起。

了解了这么多后，接着往下看代码。

OSStartHighRdy用于启动最高优先级的任务，它被OSStart()函数调用，调用前系统中必须至少有一个用户任务，否则系统发生崩溃。

```OSStartHighRdy
    LDR     R0, =NVIC_SYSPRI14                                  
                                                ; 装载系统异常优先级寄存器PRI_14，即要设置PendSV的中断优先级的寄存器
    LDR     R1, =NVIC_PENDSV_PRI                ; 装载PendSV的优先级为255
    STRB    R1, [R0]                            ; 

    MOVS    R0, #0                              ; 将数值0赋值到R0寄存器
    MSR     PSP, R0                             ; 将R0的内容(0)加载到PSP

    LDR     R0, =OS_CPU_ExceptStkBase           ; 
    LDR     R1, [R0]
    MSR     MSP, R1    

    LDR     R0, =OSRunning                      ; OSRunning = TRUE
    MOVS    R1, #1
    STRB    R1, [R0]

    LDR     R0, =NVIC_INT_CTRL                  ; 装载中断控制及状态寄存器ICSR的地址
    LDR     R1, =NVIC_PENDSVSET                 ; 中断控制及状态寄存器ICSR的位28
    STR     R1, [R0]                            ; 设置中断控制及状态寄存器ICSR位28为1,以悬起(允许)PendSV 中

    CPSIE   I                                   ; 开中断

OSStartHang
    B       OSStartHang                         ; 等价于 while(1); 以等待中断发生```


有了前面任务切换的认识后，上面的代码很容易理解，只是将PSP设置为0这个有点费解。

那么PSP是什么？跟PSP相关联还有一个MSP。
(1) MSP是主堆栈指针，或写成SP_main，这是缺省的堆栈指针，由OS内核、异常服务函数以及具有特权的APP代码使用。MSP在任务切换时是不需要保存的。
(2) PSP是进程堆栈指针，或写成SP_process，用于常规的APP代码(不处于异常服务函数中)

如何知道当前使用的是PSP还是MSP?CM3的设计是，LR寄存器的BIT2指示了当前使用的是PSP还是MSP(1表示PSP,0表示MSP)，LR本身用户保存函数的返回地址的，但是STM32是32BIT单片机，地址是32BIT的，四字节对齐，所以最后两位恒为0，所以最后两位可以拿来复用。

这里将PSP设置为0，说明系统刚刚运行，方便后面的判断OS从初始化过来的。

6. os自己使用的使能悬起PendSVd的函数

```OSCtxSw
    LDR     R0, =NVIC_INT_CTRL
    LDR     R1, =NVIC_PENDSVSET
    STR     R1, [R0]
    BX      LR```

这个函数是给os自己使用的切换任务，实质只是使能pendSV悬起(在pendSV服务中切换)，可以发现这个使能操作跟在OSStartHighRdy的实现是一样的。在os_core.c的OS_Sched()中调用，(被宏定义为OS_TASK_SW())，OS_Sched()用于启动任务调度功能。

7. os中的在中断处理程序中实现任务切换调用的函数
```OSIntCtxSw
    LDR     R0, =NVIC_INT_CTRL                                  ; Trigger the PendSV exception (causes context switch)
    LDR     R1, =NVIC_PENDSVSET
    STR     R1, [R0]
    BX      LR```

os中的在中断处理程序中调用任务切换，但是在中断处理程序中是不可以随便调用其他有可能会被调度的东西的(实时性)，但是在中断退出后可以，所以此函数在OSIntExit()调用。其实质还是触发Pendsv。

8. PendSV服务函数
终于到PendSV服务函数了，通过上面学习知道该函数主要是实现执行上下文切换。

(1) CPU自动保存xPSR、PC、LR、R12和R0-E3寄存器到任务的堆栈中
(2) CPU的栈指针切换到主堆栈指针MSP，我们只需要判断PSP指针是否为NULL就知道此时是否是因为OS进行任务切换而进入本函数的，
因此当os第一次启动任务时，即在OSStartHighRdy()中把PSP设置为NULL，以避免os以为进行任务切换
(3) 手动保存R4-R11
(4) 将旧任务的PSP指针保存(到该任务的控制块OSTCBStkPtr)，以便下次继续任务运行时继续使用原来的栈
(5) 调用任务切换的钩子函数(钩子函数在下一篇文章讲解)
(6) 在就绪的众多任务中找出优先级最高的，获取其任务控制块，进而得到该任务的PSP指针
(7) 恢复新任务的栈的R4-R11，其他的寄存器CPU会自动帮我们恢复
(8) 函数返回，新任务得到执行

```OS_CPU_PendSVHandler
    CPSID   I                                                   ; 关闭中断
    MRS     R0, PSP                                             ; 判断PSP是否为零，为零跳转OS_CPU_PendSVHandler_nosave
    CBZ     R0, OS_CPU_PendSVHandler_nosave

;硬件已经自动帮我们保存除了r4-r11的寄存器，我们只需要保存r4-r11。注意，硬件是帮我们保存到栈指针的，栈指针指向的是栈顶，
;所以栈顶下的32字节已经被使用，所以现在我们要将r4-r11保存到32字节之后，也就是要将0x20之后的栈
    SUBS    R0, R0, #0x20                                       ; Save remaining regs r4-11 on process stack
    STM     R0, {R4-R11}

;OSTCBCur结构体的首元素是OSTCBStkPtr，它是用来保存psp指针的，在这里直接取OSTCBCur其实等价于取OSTCBCur的首元素的值
    LDR     R1, =OSTCBCur                                       ; OSTCBCur->OSTCBStkPtr = SP;
    LDR     R1, [R1]
    STR     R0, [R1]                                            ; R0 is SP of process being switched out

                                                                ; At this point, entire context of process has been saved
OS_CPU_PendSVHandler_nosave
    PUSH    {R14}                                               ; r14即lr，存放函数返回地址 
    LDR     R0, =OSTaskSwHook                                   ; OSTaskSwHook();调用用户可自定实现的钩子函数
    BLX     R0
    POP     {R14}

    LDR     R0, =OSPrioCur                                      ; OSPrioCur = OSPrioHighRdy;
    LDR     R1, =OSPrioHighRdy
    LDRB    R2, [R1]
    STRB    R2, [R0]

    LDR     R0, =OSTCBCur                                       ; OSTCBCur  = OSTCBHighRdy;
    LDR     R1, =OSTCBHighRdy
    LDR     R2, [R1]
    STR     R2, [R0]

    LDR     R0, [R2]                                            ; R0 is new process SP; SP = OSTCBHighRdy->OSTCBStkPtr;
    LDM     R0, {R4-R11}                                        ; LDM是出栈，恢复r4-r11  
    ADDS    R0, R0, #0x20                                       ; 加上0x20目的是让栈指针指向栈顶
    MSR     PSP, R0                                             ; 将栈顶指针赋给PSP  
    ORR     LR, LR, #0x04                                       ; 判断是MSP还是PSP，1表PSP。这个操作只是给予其他函数的判断提供依据 
    CPSIE   I
    BX      LR    ```


需要注意的是，ARM的硬件特性，进行上下文切换时，CPU 会自动保存xPSR, PC, LR, R12, R0-R3，R4-R11需要使用程序保存。当是系统刚开始运行时候，R4-R11存放是没有用的数据，所以不需要报错。判断是系统刚开始运行第一次进行上下文切换还是非第一次进行上下文切换的依据是看PSP是否等于0。

---

