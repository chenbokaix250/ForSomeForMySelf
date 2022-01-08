# uCOS-II系统中的任务调度

在`os_cpu_a.asm`源码分析中看到了任务切换的函数OSCtxSw：

```OSCtxSw                           
    LDR     R0, =NVIC_INT_CTRL                         
    LDR     R1, =NVIC_PENDSVSET
    STR     R1, [R0]
    BX      LR
    ```
此函数是操作系统自己使用的任务切换函数，实质上只是触发pendSV，在pendSV中断服务函数在实现真正的切换任务。

pendSV的中断服务函数实现体为：

```OS_CPU_PendSVHandler
    CPSID   I                                         
    MRS     R0, PSP                                            
    CBZ     R0, OS_CPU_PendSVHandler_nosave 

    SUBS    R0, R0, #0x20                                      
    STM     R0, {R4-R11}
    ;...
    END
```

在系统运行中，操作系统总要自己去切换任务(而非一定得等systick超时)，例如某任务阻塞的获取某事件获取不到时候，系统就要切换任务。系统调用的函数是OS_Sched()，其实现体为：

```void  OS_Sched (void)
{
#if OS_CRITICAL_METHOD == 3       
    OS_CPU_SR  cpu_sr = 0;
#endif
    OS_ENTER_CRITICAL();
    if (OSIntNesting == 0) { 
        if (OSLockNesting == 0) { 
            OS_SchedNew();      /* 查表运算得出要运行的任务 */
            if (OSPrioHighRdy != OSPrioCur) { 
                OSTCBHighRdy = OSTCBPrioTbl[OSPrioHighRdy];
#if OS_TASK_PROFILE_EN > 0
                OSTCBHighRdy->OSTCBCtxSwCtr++; 
#endif
                OSCtxSwCtr++; 
                OS_TASK_SW();   /* 执行操作系统正常的任务切换 */
            }
        }
    }
    OS_EXIT_CRITICAL();
}
```
此函数首先调用OS_SchedNew()找出当前系统优先级的任务，将其优先级赋值给全局变量OSTCBHighRdy，接着调用OS_TASK_SW()进行当前任务和OSTCBHighRdy标记的优先级的任务切换。OS_TASK_SW()是一个宏：

`#define  OS_TASK_SW()         OSCtxSw() /* 操作系统任务切换 ctx表context，上下文 */`

实质就是上面讲到的在os_cpu_a.asm实现的单纯触发pendSVOSCtxSw。

在CPU中有一个特殊功能的寄存器–程序运行指针PC，它用户指向运行的程序的，CPU要运行新的任务，就必须要让PC指针获得新任务的运行地址(或者说断点地址)。既然如此，被中止运行的任务就应该把自身的PC指针的内容保压入自身堆栈中；而对待运行的任务而言，就应该把任务堆栈中上次任务被中止时存放在堆栈的PC指针的内容压入PC寄存器。但是目前的处理器并不可以对PC寄存器的内容进行压栈和出栈。要想保留PC寄存器的内容，可行的办法就是引发一次中断(或者一次函数调用)，OSCtxSw()就触发了一个pendSVOSCtxSw中断，系统在跳转到中断服务函数时，会自动地将PC指针压入堆栈，中断处理函数返回时也能将PC指针出栈，这样就可以实现PC指针的保存与恢复了。

---
