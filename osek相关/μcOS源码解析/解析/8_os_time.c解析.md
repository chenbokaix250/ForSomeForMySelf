# os_time.c

`os_time.c`卫浴Source文件夹中,该文件是系统时间相关的实现

由于嵌入式系统的任务是一个无限循环，而uCOS-II是一个抢占式内核，所以为了能让高优先级的任务不一直独占CPU，应该适当的让出CPU以给其他优先级较低的任务获得CPU得以执行。所谓“让出”即使任务进入延时，在延时期间让出CPU。

1. 延时函数OSTimeDly()

```void  OSTimeDly (INT32U ticks)
{
    INT8U      y;
#if OS_CRITICAL_METHOD == 3u    /* 临界区保护，需要使用变量cpu_sr */
    OS_CPU_SR  cpu_sr = 0u;
#endif

    if (OSIntNesting > 0u) {    /* OSIntNesting为中断嵌套的层数，表示是在某个ISR调用的 */
        return;
    }
    if (OSLockNesting > 0u) {   /* 加锁时OSLockNesting会大于0 */
        return;
    }
    if (ticks > 0u) {           /* 大于0才是有效延时 */
        OS_ENTER_CRITICAL();
        y            =  OSTCBCur->OSTCBY;   /* 将当前任务在任务就绪表中标志位非就绪态，让出CPU */
        OSRdyTbl[y] &= (OS_PRIO)~OSTCBCur->OSTCBBitX;
        if (OSRdyTbl[y] == 0u) {
            OSRdyGrp &= (OS_PRIO)~OSTCBCur->OSTCBBitY;
        }
        OSTCBCur->OSTCBDly = ticks; /* 延时节拍数存入当前任务的TCB */
        OS_EXIT_CRITICAL();         /* 退出临界区 */
        OS_Sched();                 /* 当前任务已经处于挂起态，调度后轮到次于当前优先级的就绪任务执行 */
    }
}
```

函数的参数ticks是以系统节拍数为单位的延时时间设置值，延时期间会让出CPU供其他任务使用。一般我们设置硬件tick为10ms产生一次sysytick中断，所以此函数存在缺陷：不能延时小于10ms且延时的时间需是10ms的整数倍。

2. 延时函数OSTimeDlyHMSM()
```#if OS_TIME_DLY_HMSM_EN > 0u
INT8U  OSTimeDlyHMSM (INT8U   hours,
                      INT8U   minutes,
                      INT8U   seconds,
                      INT16U  ms)
{
    INT32U ticks;
    if (OSIntNesting > 0u) {         
        return (OS_ERR_TIME_DLY_ISR);
    }
    if (OSLockNesting > 0u) {
        return (OS_ERR_SCHED_LOCKED);
    }
#if OS_ARG_CHK_EN > 0u      //OS_ARG_CHK_EN为参数检查宏
    //hours、minutes、seconds、ms都为0那就不要延时了
    if (hours == 0u) {
        if (minutes == 0u) {
            if (seconds == 0u) {
                if (ms == 0u) {
                    return (OS_ERR_TIME_ZERO_DLY);
                }
            }
        }
    }
    //参数合法检查
    if (minutes > 59u) {
        return (OS_ERR_TIME_INVALID_MINUTES);  
    }
    if (seconds > 59u) {
        return (OS_ERR_TIME_INVALID_SECONDS);
    }
    if (ms > 999u) {
        return (OS_ERR_TIME_INVALID_MS);
    }
#endif

    /* 根据输入参数，四舍五入推算tick数 */
    ticks = ((INT32U)hours * 3600uL + (INT32U)minutes * 60uL + (INT32U)seconds) * OS_TICKS_PER_SEC
          + OS_TICKS_PER_SEC * ((INT32U)ms + 500uL / OS_TICKS_PER_SEC) / 1000uL;

    /* 调用上面的延时函数OSTimeDly() */
    OSTimeDly(ticks);
    return (OS_ERR_NONE);
}
#endif
```
为了能使用日常习惯的方法来使任务延时，uCOS-II还提供了OSTimeDlyHMSM函数，该函数可以指定时分秒、毫秒进行延时。其中OS_TICKS_PER_SEC变量指明每秒钟发生几次systick，1ms产生一次systick，那么1秒就是1000次。

3. 中止任务继续延时函数OSTimeDlyResume()
```#if OS_TIME_DLY_RESUME_EN > 0u
INT8U  OSTimeDlyResume (INT8U prio)
{
    OS_TCB    *ptcb;
#if OS_CRITICAL_METHOD == 3u 
    OS_CPU_SR  cpu_sr = 0u;
#endif

    if (prio >= OS_LOWEST_PRIO) {       //参数合法性判断
        return (OS_ERR_PRIO_INVALID);
    }
    OS_ENTER_CRITICAL();                //进入临界区
    ptcb = OSTCBPrioTbl[prio];          //从就绪表中取出任务的TCB

    if (ptcb == (OS_TCB *)0) {          //为NULL表就绪表中没有此任务
        OS_EXIT_CRITICAL();
        return (OS_ERR_TASK_NOT_EXIST); 
    }
    if (ptcb == OS_TCB_RESERVED) {      //为OS_TCB_RESERVED表该不存在该任务，任务块ptcb被其他任务占用
        OS_EXIT_CRITICAL();
        return (OS_ERR_TASK_NOT_EXIST); 
    }
    if (ptcb->OSTCBDly == 0u) {         //为0表示不延时
        OS_EXIT_CRITICAL();
        return (OS_ERR_TIME_NOT_DLY);   
    }

    ptcb->OSTCBDly = 0u;   /* OSTCBDly被赋值为0，表不再延时 */

    //阻塞和挂起的判断：
    if ((ptcb->OSTCBStat & OS_STAT_PEND_ANY) != OS_STAT_RDY) {              
    //判断是否是因为等待某事件的到来而延时，不等则说明是
        ptcb->OSTCBStat     &= ~OS_STAT_PEND_ANY;              /* 清除挂起标志 */
        ptcb->OSTCBStatPend  =  OS_STAT_PEND_TO;               /* 指示不再等待的原因是因为超时  */
    } else {                                                   // 延时调用延时函数而引起的
        ptcb->OSTCBStatPend  =  OS_STAT_PEND_OK;               // 结束等待的原因是等待结束了
    }

    /* 若任务不是被阻塞，而是挂起状态，设置该任务在就绪表中设置为就绪状态 */
    if ((ptcb->OSTCBStat & OS_STAT_SUSPEND) == OS_STAT_RDY) {  /* Is task suspended?                   */
        OSRdyGrp               |= ptcb->OSTCBBitY;             /* No,  Make ready                      */
        OSRdyTbl[ptcb->OSTCBY] |= ptcb->OSTCBBitX;
        OS_EXIT_CRITICAL();
        OS_Sched();                                            /* See if this is new highest priority  */
    } else {
        OS_EXIT_CRITICAL();                                    /* Task may be suspended                */
    }
    return (OS_ERR_NONE);
}
#endif
```

任务调用了OSTimeDly()/OSTimeDlyHMSM()函数，当规定的延时时间超时，或者其他任务调用OSTimeDlyResume()取消其延时，该任务就会进入就绪状态。参数prio用于指定被取消延时的任务的优先级。
在这里，总结PEND和SUSPEND状态的差别：
(1) PEND为阻塞之意，任务在PEND过程中会释放CPU资源，其它任务可以得到执行。PEND一般在等待某个事件的出现。SUSPEND为暂停、挂起之意，任务在SUSPEND过程中不释放CPU资源。一般挂起用于程序调试中的条件中断，即出现某个条件的情况下挂起，然后进行单步调试。
(2) 挂起是一种主动行为，因此恢复也应该主动完成。阻塞是一种被动行为，被阻塞的任务不知道自己什么时候被挂起了，也不知道什么时候能恢复。
(3) PEND和NOTPEND/PEND_OK/PEND_TO对应
(4) SUSPEND和RDY对应

4. 读取时间函数OSTimeGet()
```#if OS_TIME_GET_SET_EN > 0
INT32U  OSTimeGet (void)
{
    INT32U     ticks;
#if OS_CRITICAL_METHOD == 3  
    OS_CPU_SR  cpu_sr = 0;
#endif

    OS_ENTER_CRITICAL();
    ticks = OSTime;
    OS_EXIT_CRITICAL();
    return (ticks);
}
#endif
```

为了方便，系统定义了一个INT32U类型的全局变量OSTime来记录系统发生的时钟节拍数。OSTime在应用程序中调用的OSStart()时被初始化为0，之后每发生一个时钟节拍，OSTime的值就会被加1。OSTimeGet()的返回OSTimeGet的值。

5. 设置时间函数OSTimeSet()
```#if OS_TIME_GET_SET_EN > 0
void  OSTimeSet (INT32U ticks)
{
#if OS_CRITICAL_METHOD == 3
    OS_CPU_SR  cpu_sr = 0;
#endif
    OS_ENTER_CRITICAL();
    OSTime = ticks;
    OS_EXIT_CRITICAL();
}
#endif
```

OSTimeSet()用于设置OSTime的值。
这5个函数还是比较简单，都是c语言基础，个人觉得关键主要还是在PEND和SUSPEND的理解。

---