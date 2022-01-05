# os_cpu_c.c

代码地址:
`uC-OS2/Ports/ARM-Cortex-M/ARMv6-M/ARM/os_cpu_c.c`

os_cpu_c.c定义了9个钩子(Hook)函数和一个堆栈初始化函数。

所谓钩子函数，是那些插入到某些函数中以扩展这些功能的函数，一般钩子函数是为第三方软件开发人员提供的扩充软件功能的入口。为了系统使用者扩展系统功能，uCOS-II中提供很多的钩子函数，使用者可以不修改uCOS-II的源码，只是往对应的钩子函数添加代码即可扩充uCOS-II的功能。

虽说uCOS-II提供了许多钩子函数，但在实际移植我们可以实现的也就9个，这9个就位于当前文件os_cpu_c.c。钩子函数的声明是必须的，但不是必须定义。

1. 系统定时器SysTick寄存器定义
```/*
*********************************************************************************************************
*                                          SYS TICK DEFINES
*********************************************************************************************************
*/

#define  OS_CPU_CM3_NVIC_ST_CTRL    (*((volatile INT32U *)0xE000E010uL)) /* SysTick Ctrl & Status Reg. */
#define  OS_CPU_CM3_NVIC_ST_RELOAD  (*((volatile INT32U *)0xE000E014uL)) /* SysTick Reload  Value Reg. */
#define  OS_CPU_CM3_NVIC_ST_CURRENT (*((volatile INT32U *)0xE000E018uL)) /* SysTick Current Value Reg. */
#define  OS_CPU_CM3_NVIC_ST_CAL     (*((volatile INT32U *)0xE000E01CuL)) /* SysTick Cal     Value Reg. */
#define  OS_CPU_CM3_NVIC_PRIO_ST    (*((volatile INT8U  *)0xE000ED23uL)) /* SysTick Handler Prio  Reg. */

#define  OS_CPU_CM3_NVIC_ST_CTRL_COUNT                    0x00010000uL   /* Count flag.                */
#define  OS_CPU_CM3_NVIC_ST_CTRL_CLK_SRC                  0x00000004uL   /* Clock Source.              */
#define  OS_CPU_CM3_NVIC_ST_CTRL_INTEN                    0x00000002uL   /* Interrupt enable.          */
#define  OS_CPU_CM3_NVIC_ST_CTRL_ENABLE                   0x00000001uL   /* Counter mode.              */
#define  OS_CPU_CM3_NVIC_PRIO_MIN                               0xFFu    /* Min handler prio.          */```

2. 系统初始化函数开头时会调用的钩子函数
```#if OS_CPU_HOOKS_EN > 0u    //OS_CPU_HOOKS_EN宏在os_cfg.h中
//系统初始化函数OSInit()开头调用
void  OSInitHookBegin (void)    //系统初始化函数开头的钩子函数
{
    INT32U   size;
    OS_STK  *pstk;

    /* Clear exception stack for stack checking.*/
    pstk = &OS_CPU_ExceptStk[0];
    size = OS_CPU_EXCEPT_STK_SIZE;
    while (size > 0u) {
        size--;
       *pstk++ = (OS_STK)0;
    }

    OS_CPU_ExceptStkBase = &OS_CPU_ExceptStk[OS_CPU_EXCEPT_STK_SIZE - 1u];

#if OS_TMR_EN > 0u
    OSTmrCtr = 0u;  //当使用os_tmr.c定时器管理模块，初始化系统节拍计数数量OSTmrCtr为0，每个节拍会使得OSTmrCtr加1
#endif
}
#endif```

OS_CPU_HOOKS_EN是以操作系统配置宏。在uCOS-II中，类似于xxxx_EN这样的宏都是操作系统配置宏，它们一般被宏定义在os_cpu_cfg.h文件中。用于裁剪系统功能。这个文件理论是需要系统使用者编写的，但是我们一般采用移植的方法，使用现有的文件加以修改即可。

OS_CPU_HOOKS_EN大于0表示当前系统使用了钩子函数这个功能。下来的8个钩子函数也都有OS_CPU_HOOKS_EN的判断操作。

3. 系统初始化函数结束时会调用的钩子函数
```#if OS_CPU_HOOKS_EN > 0u
void  OSInitHookEnd (void)  //系统初始化函数结束的钩子函数
{
}
#endif```

4. 创建任务时会调用的钩子函数
```#if OS_CPU_HOOKS_EN > 0u
void  OSTaskCreateHook (OS_TCB *ptcb)   //创建任务的钩子函数
{
#if OS_APP_HOOKS_EN > 0u            //若有定义应用任务
    App_TaskCreateHook(ptcb);       //调用应用任务创建的钩子函数
#else                               //否则
    (void)ptcb;                     //告诉编译器ptcb没有用到。
#endif
}
#endif```

这个函数是在OSTaskCreate()或OSTaskCreateExt()中调用的。

5. 删除任务时会调用的钩子函数
```#if OS_CPU_HOOKS_EN > 0u
void  OSTaskDelHook (OS_TCB *ptcb)
{
#if OS_APP_HOOKS_EN > 0u
    App_TaskDelHook(ptcb);
#else
   (void)ptcb; 
#endif
}
#endif```

6. 空闲任务调用的钩子函数
```#if OS_CPU_HOOKS_EN > 0u
void  OSTaskIdleHook (void) //空闲任务钩子函数
{
#if OS_APP_HOOKS_EN > 0u
    App_TaskIdleHook();
#endif
}
#endif```

7. 任务返回时调用的钩子函数
```#if OS_CPU_HOOKS_EN > 0u
void  OSTaskReturnHook (OS_TCB  *ptcb)  //任务返回的钩子函数
{
#if OS_APP_HOOKS_EN > 0u
    App_TaskReturnHook(ptcb);
#else
    (void)ptcb;
#endif
}
#endif```

8. 统计任务调用的钩子函数
```#if OS_CPU_HOOKS_EN > 0u
void  OSTaskStatHook (void) //统计任务钩子函数
{
#if OS_APP_HOOKS_EN > 0u
    App_TaskStatHook();
#endif
}
#endif```

9. 任务堆结构初始化函数
c语言的函数运行需要栈来支持，局部变量就是栈这种数据结构来实现的。栈其实就是os管理内存的一种方式，os是通过栈指针sp来管理栈内存的。在单片机裸机程序中，整个程序使用一个栈，这个栈是跟main共用的栈。在os中则不一样，因为os中有任务的概念，任务在宏观上实现并行，需要现场的保护和恢复，所以不同的任务就不能共用栈。每个任务都要自己的私有栈。

```OS_STK *OSTaskStkInit (void (*task)(void *p_arg), void *p_arg, OS_STK *ptos, INT16U opt)
{
    OS_STK *stk;


    (void)opt;                                   /* 'opt' 并没有用到，防止编译器提示警告  */
    stk       = ptos;                            /* 加载栈指针 */

    //发生中断后，xPSR, PC, LR, R12, R3-R0被自动保存在栈中    
    *(stk)    = (INT32U)0x01000000uL;            /* xPSR                                               */
    *(--stk)  = (INT32U)task;                    /* Entry Point(任务的入口)                            */
    *(--stk)  = (INT32U)OS_TaskReturn;           /* R14 (LR)                                           */
    *(--stk)  = (INT32U)0x12121212uL;            /* R12                                                */
    *(--stk)  = (INT32U)0x03030303uL;            /* R3                                                 */
    *(--stk)  = (INT32U)0x02020202uL;            /* R2                                                 */
    *(--stk)  = (INT32U)0x01010101uL;            /* R1                                                 */
    *(--stk)  = (INT32U)p_arg;                   /* R0 : 变量                                          */

    /* 剩下的寄存器需要手动保存在堆栈         */                                             
    *(--stk)  = (INT32U)0x11111111uL;            /* R11                                                */
    *(--stk)  = (INT32U)0x10101010uL;            /* R10                                                */
    *(--stk)  = (INT32U)0x09090909uL;            /* R9                                                 */
    *(--stk)  = (INT32U)0x08080808uL;            /* R8                                                 */
    *(--stk)  = (INT32U)0x07070707uL;            /* R7                                                 */
    *(--stk)  = (INT32U)0x06060606uL;            /* R6                                                 */
    *(--stk)  = (INT32U)0x05050505uL;            /* R5                                                 */
    *(--stk)  = (INT32U)0x04040404uL;            /* R4                                                 */

    return (stk);
}```

OSTaskStkInit()的作用就是对任务的栈内存进行初始化，我们每创建一个任务，都应该调用这个函数对任务的私有栈进行初始化，之后再去使用。
参数1: 指向任务的执行代码
参数2: 传给任务的调用时的参数
参数3: ptos指向栈顶
ARM是满降栈，也就是sp指针指向的内容都是满的，但是一开始ptos指向的是栈的最上方，而刚开始的时候该位置肯定为空，所以ptos指向的是”free”的。
参数4: 可选项，起到改变函数行为的效果，这是用于扩展的。但是uCOS-II暂时没用到。

在CM3内核中，函数发生中断后，xPSR，PC，LR，R12，R3-R0会被自动保存到栈中，R11-R4如果需要保存，需要手动保存。OSTaskStkInit()既然是在初始化这份栈，所以需要模拟被中断后的样子。代码中，R1-R12、R4-R11都没什么意义，目的在于方便调试，但是，
(1) xPSR=0x01000000L，xPSR的T位(第24位)置1，否则第一次执行任务时就Fault
(2) PC必须指向任务入口
(3) R14=任务返回函数
(4) R0用于传递任务的参数，等于p_arg

10. 切换任务时被调用的钩子函数
```#if (OS_CPU_HOOKS_EN > 0u) && (OS_TASK_SW_HOOK_EN > 0u)
void  OSTaskSwHook (void)   //切换任务时被调用的钩子函数
{
#if OS_APP_HOOKS_EN > 0u    //如果有定义应用任务
    App_TaskSwHook();       //应用任务切换调用的钩子函数
#endif
}
#endif```

11. 初始任务控制块化时调用的钩子函数
```#if OS_CPU_HOOKS_EN > 0u
void  OSTCBInitHook (OS_TCB *ptcb)  //初始任务控制块化时调用的钩子函数
{
#if OS_APP_HOOKS_EN > 0u
    App_TCBInitHook(ptcb);
#else
    (void)ptcb;
#endif
}
#endif```

TCB即Task Control Block，任务控制块，记录了系统中每个任务的状态、属性信息。

12. 时钟节拍到了以后调用的钩子函数
```#if (OS_CPU_HOOKS_EN > 0u) && (OS_TIME_TICK_HOOK_EN > 0u)
void  OSTimeTickHook (void)
{
#if OS_APP_HOOKS_EN > 0u
    App_TimeTickHook();         //应用程序的时钟节拍钩子函数
#endif

#if OS_TMR_EN > 0u              //如果有启动定时器管理
    OSTmrCtr++;                 //计时全局变量OSTmrCtr自加1

    //如果时间到了
    if (OSTmrCtr >= (OS_TICKS_PER_SEC / OS_TMR_CFG_TICKS_PER_SEC)) {
        OSTmrCtr = 0;   //计时清零
        OSTmrSignal();  //发送信号量OSTmrSignal(初始值为0)
                        //以便软件定时器扫面任务OSTmr-Task能请求到信号量继续运行
    }
#endif
}
#endif```

13. SysTick超时后执行的函数
```void  OS_CPU_SysTickHandler (void)
{
    /* 进入临界区，OSIntNesting是全局变量，操作该变量时希望不被中断打扰 */
    OS_CPU_SR  cpu_sr;
    OS_ENTER_CRITICAL();                         /* Tell uC/OS-II that we are starting an ISR          */

    OSIntNesting++;

    /* 退出临界区 */
    OS_EXIT_CRITICAL();

    OSTimeTick();                                /* Call uC/OS-II's OSTimeTick()                       */

    OSIntExit();                                 /* Tell uC/OS-II that we are leaving the ISR          */
}```

14. 初始化SysTick定时器
```void  OS_CPU_SysTickInit (INT32U  cnts)
{
    //使能SysTick定时器
    OS_CPU_CM3_NVIC_ST_RELOAD = cnts - 1u;

    /* Set prio of SysTick handler to min prio.           */
    //使能SysTick定时器中断
    OS_CPU_CM3_NVIC_PRIO_ST   = OS_CPU_CM3_NVIC_PRIO_MIN;
                                                 /* Enable timer.                                      */
    OS_CPU_CM3_NVIC_ST_CTRL  |= OS_CPU_CM3_NVIC_ST_CTRL_CLK_SRC | OS_CPU_CM3_NVIC_ST_CTRL_ENABLE;
                                                 /* Enable timer interrupt.                            */
    OS_CPU_CM3_NVIC_ST_CTRL  |= OS_CPU_CM3_NVIC_ST_CTRL_INTEN;
}```

OS_CPU_SysTickInit会被第一个任务调用，用于初始化SysTick定时器。

OS_CPU_SysTickHandler(void)和OS_CPU_SysTickInit (INT32U cnts)在移植的时候，我们会注释掉，取而代之的是STM32标准外设库的函数。

在本文件中，涉及到任务的很多概念，如TCB任务控制块、任务调度、统计/空闲任务等，这些将在下来的文章中介绍。

---
