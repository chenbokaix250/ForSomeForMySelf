# os_mutex.c的解析

[toc]
 
定位到uCOS-II/Source/os_mutex.c，该文件是互斥型信号量的相关操作函数。
互斥型信号量也就是互斥锁Mutex，是一个二值(0/1)信号量。在操作共享资源时，使用Mutex可以保证满足互斥条件。

>互斥锁: 对共享数据进行锁定，保证同一时刻只能有一个线程去操作。
注意: 互斥锁是多个线程一起去抢，抢到锁的线程先执行，没有抢到锁的线程需要等待，等互斥锁使用完释放后，其它等待的线程再去抢这个锁。

## 1.非阻塞的获取互斥型信号量函数OSMutexAccept()

OSMutexAccept()用于检测Mutex以判断是否可用，若资源不可用，调用此函数不会使得所在任务被挂起。

```
//允许使用os中的Mutex
#if OS_MUTEX_ACCEPT_EN > 0u
BOOLEAN  OSMutexAccept (OS_EVENT  *pevent,  //pevent指向管理着某资源的Mutex，
                        INT8U     *perr)    //perr为输出型参数用于表示出错类型
{
    INT8U      pcp;

    //临界区保护方法3
#if OS_CRITICAL_METHOD == 3u
    OS_CPU_SR  cpu_sr = 0u;
#endif

#ifdef OS_SAFETY_CRITICAL
    if (perr == (INT8U *)0) {
        OS_SAFETY_CRITICAL_EXCEPTION(); //与系统异常相关，找不到定义，不细究
        return (OS_FALSE);
    }
#endif

//检测参数宏使能
#if OS_ARG_CHK_EN > 0u
    if (pevent == (OS_EVENT *)0) {
        *perr = OS_ERR_PEVENT_NULL;
        return (OS_FALSE);
    }
#endif
    //本函数是支持MUTEX的，若非OS_EVENT_TYPE_MUTEX，返回错误
    if (pevent->OSEventType != OS_EVENT_TYPE_MUTEX) {
        *perr = OS_ERR_EVENT_TYPE;
        return (OS_FALSE);
    }
    //不能再ISR中试图获取二值信号量
    if (OSIntNesting > 0u) {
        *perr = OS_ERR_PEND_ISR;
        return (OS_FALSE);
    }

    //进入临界区
    OS_ENTER_CRITICAL();
    //高8位为天花板优先级，其优先等级大于所有可以获取该Mutex的任务的优先级
    pcp = (INT8U)(pevent->OSEventCnt >> 8u);    

    //低8位全为1表示该Mutex没有被任务获取过，Mutex可用
    if ((pevent->OSEventCnt & OS_MUTEX_KEEP_LOWER_8) == OS_MUTEX_AVAILABLE) {

        //将天花板优先级设置到pevent->OSEventCnt，其实这句话不起效果，
        //pevent->OSEventCnt本来就为天花板优先级
        pevent->OSEventCnt &= OS_MUTEX_KEEP_UPPER_8;

        //将任务优先级设置到低8位，以表示该互斥锁被任务获取了
        pevent->OSEventCnt |= OSTCBCur->OSTCBPrio;

        //将事件控制块连接到该任务控制块
        pevent->OSEventPtr  = (void *)OSTCBCur; 

        if ((pcp != OS_PRIO_MUTEX_CEIL_DIS) &&  //OS_PRIO_MUTEX_CEIL_DIS表示禁用将优先级提升天花板 
            (OSTCBCur->OSTCBPrio <= pcp)) {     //天花板的优先级必须不小于获取该Mutex的任务，否则说明在创建Mutex的时候
                                                //天花板优先级设置出错
             OS_EXIT_CRITICAL();
            *perr = OS_ERR_PCP_LOWER;
        } else {
             OS_EXIT_CRITICAL();
            *perr = OS_ERR_NONE;                //正常执行
        }
        return (OS_TRUE);
    }
    OS_EXIT_CRITICAL();
    *perr = OS_ERR_NONE;
    return (OS_FALSE);
}
#endif
```

## 2. 创建和初始化互斥型信号量函数OSMutexCreate()

互斥型信号量mutual的建立和初始化. 在操作共享资源时, 使用Mutex可以保证满足互斥条件。

```
OS_EVENT  *OSMutexCreate (INT8U   prio,     //用于设置Mutex的天花板优先级
                          INT8U  *perr)     //用于输出错误信息      
{
    OS_EVENT  *pevent;
#if OS_CRITICAL_METHOD == 3u
    OS_CPU_SR  cpu_sr = 0u;
#endif

#ifdef OS_SAFETY_CRITICAL
    if (perr == (INT8U *)0) {
        OS_SAFETY_CRITICAL_EXCEPTION();
        return ((OS_EVENT *)0);
    }
#endif

#ifdef OS_SAFETY_CRITICAL_IEC61508
    if (OSSafetyCriticalStartFlag == OS_TRUE) {
        OS_SAFETY_CRITICAL_EXCEPTION();
        return ((OS_EVENT *)0);
    }
#endif

#if OS_ARG_CHK_EN > 0u
    if (prio != OS_PRIO_MUTEX_CEIL_DIS) {   //OS_PRIO_MUTEX_CEIL_DIS表禁用将优先级提升天花板
        if (prio >= OS_LOWEST_PRIO) {       //prio大于OS_LOWEST_PRIO，非法
           *perr = OS_ERR_PRIO_INVALID;
            return ((OS_EVENT *)0);
        }
    }
#endif
    if (OSIntNesting > 0u) {
        *perr = OS_ERR_CREATE_ISR; 
        return ((OS_EVENT *)0);
    }
    OS_ENTER_CRITICAL();
    if (prio != OS_PRIO_MUTEX_CEIL_DIS) {
        //判断天花板优先级对应的任务是否存在，不等于0表示存在
        if (OSTCBPrioTbl[prio] != (OS_TCB *)0) { 
            OS_EXIT_CRITICAL();
           *perr = OS_ERR_PRIO_EXIST;
            return ((OS_EVENT *)0);
        }

        //不存在则天花板优先级占据的TCB空间占据
        OSTCBPrioTbl[prio] = OS_TCB_RESERVED; 
    }

    pevent = OSEventFreeList;   //得到一个空闲的事件控制块

    //等于0表示事件控制块链表断开了
    if (pevent == (OS_EVENT *)0) {
        if (prio != OS_PRIO_MUTEX_CEIL_DIS) {
            OSTCBPrioTbl[prio] = (OS_TCB *)0;              /* No, Release the table entry              */
        }
        OS_EXIT_CRITICAL();
       *perr = OS_ERR_PEVENT_NULL;                         /* No more event control blocks             */
        return (pevent);
    }

    //指向下一个空闲事件空间
    OSEventFreeList     = (OS_EVENT *)OSEventFreeList->OSEventPtr;
    OS_EXIT_CRITICAL();

    //成功申请到一个事件链表中的节点，现在进行初始化
    pevent->OSEventType = OS_EVENT_TYPE_MUTEX;  //设置事件类型

    //高8位为天花板优先级；因为该事件现在还不被某个任务申请，所以低8位为OS_MUTEX_AVAILABLE表示该事件可用
    //若被任务申请了，则低8位为该任务的优先级
    pevent->OSEventCnt  = (INT16U)((INT16U)prio << 8u) | OS_MUTEX_AVAILABLE; 

    //OSEventPtr指向0，表示该任务没有MUTEX
    pevent->OSEventPtr  = (void *)0;
#if OS_EVENT_NAME_EN > 0u
    pevent->OSEventName = (INT8U *)(void *)"?";
#endif
    OS_EventWaitListInit(pevent);  //初始化pevent中的WaitList，即没有任务在等待该Mutex
   *perr = OS_ERR_NONE;
    return (pevent);
}

OS_EventWaitListInit()函数实现体为：
/* 初始化pevent中的 WaitList*/
#if (OS_EVENT_EN)
void  OS_EventWaitListInit (OS_EVENT *pevent)
{
#if OS_LOWEST_PRIO <= 63
    INT8U  *ptbl;
#else
    INT16U *ptbl;
#endif
    INT8U   i;

    /* 置零操作OSEventGrp和OSEventTbl */
    pevent->OSEventGrp = 0;                      /* No task waiting on event                           */
    ptbl               = &pevent->OSEventTbl[0];

    for (i = 0; i < OS_EVENT_TBL_SIZE; i++) {
        *ptbl++ = 0;
    }
}
```

## 3. 删除互斥型信号量函数OSMutexDel()

删除Mutex操作是有风险的，因为可能存在任务它还想使用这个实际上已被删除的Mutex，所以要删除一个Mutex首先应删除等待这个Mutex的所有任务。

```
#if OS_MUTEX_DEL_EN > 0u        //Mutex删除使能宏
OS_EVENT  *OSMutexDel (OS_EVENT  *pevent,   //指向Mutex的指针
                       INT8U      opt,      //删除Mutex的条件，OS_DEL_NO_PEND/OS_DEL_ALWAYS
                       INT8U     *perr)     //指向出错信息
{
    BOOLEAN    tasks_waiting;
    OS_EVENT  *pevent_return;
    INT8U      pcp;
    INT8U      prio;
    OS_TCB    *ptcb;
#if OS_CRITICAL_METHOD == 3u
    OS_CPU_SR  cpu_sr = 0u;
#endif

#ifdef OS_SAFETY_CRITICAL
    if (perr == (INT8U *)0) {
        OS_SAFETY_CRITICAL_EXCEPTION();
        return ((OS_EVENT *)0);
    }
#endif

#if OS_ARG_CHK_EN > 0u
    if (pevent == (OS_EVENT *)0) {
        *perr = OS_ERR_PEVENT_NULL;
        return (pevent);
    }
#endif
    if (pevent->OSEventType != OS_EVENT_TYPE_MUTEX) {
        *perr = OS_ERR_EVENT_TYPE;
        return (pevent);
    }
    if (OSIntNesting > 0u) {
        *perr = OS_ERR_DEL_ISR;
        return (pevent);
    }
    OS_ENTER_CRITICAL();
    //OSEventGrp不等于0表示有任务正在等待预备删除的Mutex
    if (pevent->OSEventGrp != 0u) { 
        tasks_waiting = OS_TRUE; 
    } else {
        tasks_waiting = OS_FALSE;
    }

    //根据删除条件执行删除操作
    switch (opt) {
        //OS_DEL_NO_PEND表没有任务在等待才删除，反之不删除
        case OS_DEL_NO_PEND:  
             //没任务在等待，删除之，回收该空间
             if (tasks_waiting == OS_FALSE) {
#if OS_EVENT_NAME_EN > 0u
                 pevent->OSEventName   = (INT8U *)(void *)"?";
#endif
                 //取出天花板优先级所在的任务TCB内存空间
                 pcp                   = (INT8U)(pevent->OSEventCnt >> 8u);
                 if (pcp != OS_PRIO_MUTEX_CEIL_DIS) {
                     OSTCBPrioTbl[pcp] = (OS_TCB *)0; 
                 }
                 pevent->OSEventType   = OS_EVENT_TYPE_UNUSED;
                 pevent->OSEventPtr    = OSEventFreeList;  /* Return Event Control Block to free list  */
                 pevent->OSEventCnt    = 0u;
                 OSEventFreeList       = pevent;
                 OS_EXIT_CRITICAL();
                 *perr                 = OS_ERR_NONE;
                 pevent_return         = (OS_EVENT *)0; 
             } else {  //有任务在等待，不能删除且报错
                 OS_EXIT_CRITICAL();
                 *perr                 = OS_ERR_TASK_WAITING;
                 pevent_return         = pevent;
             }
             break;

        case OS_DEL_ALWAYS:   //不管有无任务在等待该Mutex都删除
            //取出天花板优先级所在的任务TCB内存空间
             pcp  = (INT8U)(pevent->OSEventCnt >> 8u); 
             if (pcp != OS_PRIO_MUTEX_CEIL_DIS) {

                 //取出占据该Mutex的任务的原优先级
                 prio = (INT8U)(pevent->OSEventCnt & OS_MUTEX_KEEP_LOWER_8);
                 //取出占据该Mutex的任务的TCB
                 ptcb = (OS_TCB *)pevent->OSEventPtr;

                 //确实存在占据该Mutex的任务
                 if (ptcb != (OS_TCB *)0) {
                     //若该任务的优先级已经被提升至天花板，则恢复其原优先级
                     if (ptcb->OSTCBPrio == pcp) {  
                         OSMutex_RdyAtPrio(ptcb, prio); 
                     }
                 }
             }
             //环形所有在等待该Mutex的任务，不然一旦该Mutex被删除，这些任务将陷入一直等待中
             while (pevent->OSEventGrp != 0u) {
                 (void)OS_EventTaskRdy(pevent, (void *)0, OS_STAT_MUTEX, OS_STAT_PEND_ABORT);
             }

             //接下来的删除操作跟前面一样了
#if OS_EVENT_NAME_EN > 0u
             pevent->OSEventName   = (INT8U *)(void *)"?";
#endif
             pcp                   = (INT8U)(pevent->OSEventCnt >> 8u);
             if (pcp != OS_PRIO_MUTEX_CEIL_DIS) {
                 OSTCBPrioTbl[pcp] = (OS_TCB *)0;
             }
             pevent->OSEventType   = OS_EVENT_TYPE_UNUSED;
             pevent->OSEventPtr    = OSEventFreeList;
             pevent->OSEventCnt    = 0u;
             OSEventFreeList       = pevent; 
             OS_EXIT_CRITICAL();
             if (tasks_waiting == OS_TRUE) {  
                 OS_Sched(); 
             }
             *perr         = OS_ERR_NONE;
             pevent_return = (OS_EVENT *)0;
             break;

        default:
             OS_EXIT_CRITICAL();
             *perr         = OS_ERR_INVALID_OPT;    //删除条件出错
             pevent_return = pevent;
             break;
    }
    return (pevent_return);
}
#endif
```

## 4. 阻塞获取一个互斥型信号量函数OSMutexPend()

当任务需要独占共享资源时候，可以使用OSMutexPend()函数获得一个Mutex对该资源加以保护。该函数若获得到了Mutex将返回，反之调用此函数的任务进入挂起等待状态，直到获取到目标Mutex或者超时。需要注意的是，如果调用此函数获取Mutex，而该Mutex已经被低优先级任务占用了，那么此函数会将占据该Mutex的低优先级任务的优先级提升至天花板。

```void  OSMutexPend (OS_EVENT  *pevent,   //要获取的目的Mutex
                   INT32U     timeout   //超时时间
                   INT8U     *perr)
{
    INT8U      pcp;
    INT8U      mprio;
    BOOLEAN    rdy;
    OS_TCB    *ptcb;
    OS_EVENT  *pevent2;
    INT8U      y;
#if OS_CRITICAL_METHOD == 3u 
    OS_CPU_SR  cpu_sr = 0u;
#endif

#ifdef OS_SAFETY_CRITICAL
    if (perr == (INT8U *)0) {
        OS_SAFETY_CRITICAL_EXCEPTION();
        return;
    }
#endif

#if OS_ARG_CHK_EN > 0u
    if (pevent == (OS_EVENT *)0) { 
        *perr = OS_ERR_PEVENT_NULL;
        return;
    }
#endif
    if (pevent->OSEventType != OS_EVENT_TYPE_MUTEX) {
        *perr = OS_ERR_EVENT_TYPE;
        return;
    }
    if (OSIntNesting > 0u) { 
        *perr = OS_ERR_PEND_ISR;
        return;
    }
    if (OSLockNesting > 0u) { 
        *perr = OS_ERR_PEND_LOCKED; 
        return;
    }

    OS_ENTER_CRITICAL();
    //拿到天花板优先级
    pcp = (INT8U)(pevent->OSEventCnt >> 8u); 

    //等于OS_MUTEX_AVAILABLE表示该Mutex之前没有被任务任务使用过
    if ((INT8U)(pevent->OSEventCnt & OS_MUTEX_KEEP_LOWER_8) == OS_MUTEX_AVAILABLE) {
        //设置Mutex的天花板优先级
        pevent->OSEventCnt &= OS_MUTEX_KEEP_UPPER_8;

        //将任务优先级设置到低8位，以表示该互斥锁被任务获取了
        pevent->OSEventCnt |= OSTCBCur->OSTCBPrio;

        //将事件控制块连接到该任务控制块
        pevent->OSEventPtr  = (void *)OSTCBCur; 
        if ((pcp != OS_PRIO_MUTEX_CEIL_DIS) &&  //OS_PRIO_MUTEX_CEIL_DIS表示禁用将优先级提升天花板 
            (OSTCBCur->OSTCBPrio <= pcp)) {     //天花板的优先级必须不小于获取该Mutex的任务，否则说明在创建Mutex的时候
             OS_EXIT_CRITICAL();                //天花板优先级设置出错
            *perr = OS_ERR_PCP_LOWER;
        } else {
             OS_EXIT_CRITICAL();
            *perr = OS_ERR_NONE;
        }
        return;
    }

    if (pcp != OS_PRIO_MUTEX_CEIL_DIS) {
        //低8位存储了拥有该Mutex的任务的优先级
        mprio = (INT8U)(pevent->OSEventCnt & OS_MUTEX_KEEP_LOWER_8); 

        /* 一开始OSEventPtr是用来在event链表中指向下一个节点的，当Mutex有任务获取了它之后，它就没用处了，
        用来指向了获取了该Mutex的任务的TCB。所以说OSEventPtr取值有3种可能:
        (1) Mutex还没被获取时，在event链表中指向一个格子，该格子用于存放Mutex
        (2) Mutex被获取了，但是还没跟任务挂接上，取值为NULL
        (3) Mutex被获取了，且已经跟某个任务挂接上了，取值为该任务的TCB的地址 */

        //拿到当前占据该Mutex的任务的TCB
        ptcb  = (OS_TCB *)(pevent->OSEventPtr);
        if (ptcb->OSTCBPrio > pcp) { //天花板的优先级最高即数值最低，所以这个if一定会成立

            //如果当前任务的优先级大于拥有该Mutex的任务的优先级
            //这时候有可能发生任务优先级翻转，需要将拥有该Mutex的任务的优先级提升至天花板
            if (mprio > OSTCBCur->OSTCBPrio) 
            {
                y = ptcb->OSTCBY; /* 注意，ptcb是拥有Mutex的任务的tcb指针 */

                //不等于0表示就绪态
                if ((OSRdyTbl[y] & ptcb->OSTCBBitX) != 0u) { 

                    //清除就绪态，即将该任务设置为非就绪态
                    OSRdyTbl[y] &= (OS_PRIO)~ptcb->OSTCBBitX; 
                    if (OSRdyTbl[y] == 0u) {
                        OSRdyGrp &= (OS_PRIO)~ptcb->OSTCBBitY;
                    }
                    rdy = OS_TRUE;
                } 
                else   //拥有给Mutex的任务为非就绪态
                { 
                    //拿出该任务的等待事件列表
                    pevent2 = ptcb->OSTCBEventPtr;

                    //解引用前先判断是否为空指针
                    if (pevent2 != (OS_EVENT *)0) {

                        //将该任务的所有等待事件清空，其目的是让持有Mutex的任务赶快执行，执行
                        //完毕后才能轮到比它优先级高的当前任务执行
                        y = ptcb->OSTCBY;
                        pevent2->OSEventTbl[y] &= (OS_PRIO)~ptcb->OSTCBBitX;
                        if (pevent2->OSEventTbl[y] == 0u) {
                            pevent2->OSEventGrp &= (OS_PRIO)~ptcb->OSTCBBitY;
                        }
                    }
                    rdy = OS_FALSE; 
                }
                ptcb->OSTCBPrio = pcp; //提升持有Mutex的任务的优先级提升至天花板
/* 以下四个变量跟任务的优先级密切相关，所以要随之更新 */
#if OS_LOWEST_PRIO <= 63u
                ptcb->OSTCBY    = (INT8U)( ptcb->OSTCBPrio >> 3u);
                ptcb->OSTCBX    = (INT8U)( ptcb->OSTCBPrio & 0x07u);
#else
                ptcb->OSTCBY    = (INT8U)((INT8U)(ptcb->OSTCBPrio >> 4u) & 0xFFu);
                ptcb->OSTCBX    = (INT8U)( ptcb->OSTCBPrio & 0x0Fu);
#endif
                ptcb->OSTCBBitY = (OS_PRIO)(1uL << ptcb->OSTCBY);
                ptcb->OSTCBBitX = (OS_PRIO)(1uL << ptcb->OSTCBX);

                //rdy是在上面设置的，为OS_TRUE表示一开始是就绪态非后改为非就绪态，现在又要将其改为就绪态。为什么？
                //因为中间改变了任务的优先级
                if (rdy == OS_TRUE) {
                    OSRdyGrp               |= ptcb->OSTCBBitY; 
                    OSRdyTbl[ptcb->OSTCBY] |= ptcb->OSTCBBitX;
                } else { //原来在等待某事件，清除等待事件，即还是设置为就绪态
                    pevent2 = ptcb->OSTCBEventPtr;
                    if (pevent2 != (OS_EVENT *)0) { 
                        pevent2->OSEventGrp               |= ptcb->OSTCBBitY;
                        pevent2->OSEventTbl[ptcb->OSTCBY] |= ptcb->OSTCBBitX;
                    }
                }
                /* tcb没被改变，但是在OSTCBPrioTbl的位置改变了，所以这里要做修改 */
                OSTCBPrioTbl[pcp] = ptcb;

                //到这里可以察觉，天花板pip所代表的优先级所在的格子必要要空着，即不能装载任务，
                //不然这里等于ptcb就会把原来装载的pip的普通任务冲掉了 */
            }
        }

    }
    /* 标志当前任务的状态，如OS_STAT_RDY就绪态，在这里标记当前任务正在等待Mutex */
    OSTCBCur->OSTCBStat     |= OS_STAT_MUTEX;

    /* 标志当前任务被挂起态 */
    OSTCBCur->OSTCBStatPend  = OS_STAT_PEND_OK;

    /* 挂起超时时间，注意，超时后就变为OS_STAT_PEND_TO状态而非就绪态 */ 
    OSTCBCur->OSTCBDly       = timeout; 

    /* os_corec定义的，实现将当前任务因等待事件而挂起：
    (1)把当前任务在pevent中标记出来，表示当前任务正在等待event。
    (2)把当前任务从就绪表中拿出来 
    */ 
    OS_EventTaskWait(pevent);
    OS_EXIT_CRITICAL();

    //调度
    OS_Sched();
    OS_ENTER_CRITICAL();

     /* 能执行到这里说明可能：
     (1) 原先持有mutex的任务已经放开Mutex了
     (2) 等待的Mutex被删除了
     (3) 超时
     于是就有了下面的分支
     */
    switch (OSTCBCur->OSTCBStatPend) { 
        case OS_STAT_PEND_OK:
             *perr = OS_ERR_NONE;
             break;

        case OS_STAT_PEND_ABORT:
             *perr = OS_ERR_PEND_ABORT;  
             break;

        case OS_STAT_PEND_TO:
        default:
             // 超时了还等待不到，直接从pevent等待event队列中删除本任务，不再等待
             OS_EventTaskRemove(OSTCBCur, pevent);
             *perr = OS_ERR_TIMEOUT;  
             break;
    }

    //设置任务的相关状态
    OSTCBCur->OSTCBStat          =  OS_STAT_RDY; 
    OSTCBCur->OSTCBStatPend      =  OS_STAT_PEND_OK; 
    OSTCBCur->OSTCBEventPtr      = (OS_EVENT  *)0;
#if (OS_EVENT_MULTI_EN > 0u)
    OSTCBCur->OSTCBEventMultiPtr = (OS_EVENT **)0;
#endif
    OS_EXIT_CRITICAL();
}
```

## 5. 释放一个互斥型信号量函数OSMutexPost()

OSMutexPost()用于释放持有的Mutex。当任务已调用OSMutexAccept()或OSMutexPend()请求得到Mutex时，此函数才起作用。若持有Mutex的本任务的优先级已经被提升至天花板，那么此函数要恢复为原先的优先级；若有多个任务在等待被释放的Mutex，那么等待任务中优先级最高的任务获得Mutex；若没有等待该Mutex的任务那么只是设置相关的值。

```INT8U  OSMutexPost (OS_EVENT *pevent)
{
    INT8U      pcp;  
    INT8U      prio;
#if OS_CRITICAL_METHOD == 3u  
    OS_CPU_SR  cpu_sr = 0u;
#endif

    if (OSIntNesting > 0u) { 
        return (OS_ERR_POST_ISR); 
    }
#if OS_ARG_CHK_EN > 0u
    if (pevent == (OS_EVENT *)0) {
        return (OS_ERR_PEVENT_NULL);
    }
#endif
    if (pevent->OSEventType != OS_EVENT_TYPE_MUTEX) { 
        return (OS_ERR_EVENT_TYPE);
    }
    OS_ENTER_CRITICAL();

    //拿到天花板优先级
    pcp  = (INT8U)(pevent->OSEventCnt >> 8u); 

    //占据Mutex的原来优先级，也就是当前任务
    prio = (INT8U)(pevent->OSEventCnt & OS_MUTEX_KEEP_LOWER_8); 
    /*
        为什么在这里要用OSEventCnt来拿原先任务的优先级而不是像之前通过任务的TCB来拿？
        这是因为在获取Mutex的时候，本任务的优先级可能被提高了，而OSEventCnt的低8位保留了任务原来的优先级 
    */  

    //OSEventPtr是指向持有Mutex的任务，那么如果OSTCBCur不等于OSEventPtr，
    //说明当前任务并不是持有Mutex的任务，那post个毛线
    if (OSTCBCur != (OS_TCB *)pevent->OSEventPtr) {
        OS_EXIT_CRITICAL();
        return (OS_ERR_NOT_MUTEX_OWNER);
    }

    if (pcp != OS_PRIO_MUTEX_CEIL_DIS) {
        //若等于pcp说明持有Mutex的任务的优先级被提升过了
        if (OSTCBCur->OSTCBPrio == pcp) {
            //参数为当前任务的TCB、当前任务原先的优先级，即将当前任务的优先级恢复原先饿优先级
            OSMutex_RdyAtPrio(OSTCBCur, prio); 
        }
         /* 原先优先级为pcp的格子，已经不用，所以填充为OS_TCB_RESERVED */
        OSTCBPrioTbl[pcp] = OS_TCB_RESERVED;
    }

    /* 不等于0说明当前还有任务在等待Mutex，那么就要去唤醒它，如果是多个任务在等待Mutex，
    /* 那么唤醒的是众多任务中优先级最高的一个 */
    if (pevent->OSEventGrp != 0u) {
        // 得到在等待Mutex的其他任务中优先级最高的优先级prio
        prio                = OS_EventTaskRdy(pevent, (void *)0, OS_STAT_MUTEX, OS_STAT_PEND_OK);

        //将Mutex归属于在等待Mutex的其他任务中优先级最高的任务
        pevent->OSEventCnt &= OS_MUTEX_KEEP_UPPER_8;
        pevent->OSEventCnt |= prio;
        pevent->OSEventPtr  = OSTCBPrioTbl[prio]; 
        if ((pcp  != OS_PRIO_MUTEX_CEIL_DIS) &&
            (prio <= pcp)) {   //pip应该是最小的，即优先级是高的，不符合此条件返回错误信息OS_ERR_PIP_LOWER。 */ 
            OS_EXIT_CRITICAL();

            //为什么两种情况都要调用调度函数OS_Sched() ，因为这个错误并非致命，os还得继续执行
            OS_Sched();
            return (OS_ERR_PCP_LOWER);
        } else {
            OS_EXIT_CRITICAL();
            OS_Sched();
            return (OS_ERR_NONE);
        }
    }
    //执行到这里说明没有任务在等待当前任务释放的Mutex，直接走人，
    //即OSEventCnt设置为OS_MUTEX_AVAILABLE表示该Mutex闲置着
    pevent->OSEventCnt |= OS_MUTEX_AVAILABLE;
    pevent->OSEventPtr  = (void *)0;
    OS_EXIT_CRITICAL();
    return (OS_ERR_NONE);
}
```

## 6. 获取Mutex的当前状态信息函数OSMutexQuery()

Mutex的信息存放于p_mutex_data中，函数调用者应先为其分配OS_MUTEX_DATA的数据空间。

```#if OS_MUTEX_QUERY_EN > 0
INT8U  OSMutexQuery (OS_EVENT *pevent,      //指向管理某资源的互斥型信号量
                     OS_MUTEX_DATA *p_mutex_data) //输出型参数，用于存放Mutex的状态信息
{
    INT8U      i;
#if OS_LOWEST_PRIO <= 63
    INT8U     *psrc;
    INT8U     *pdest;
#else
    INT16U    *psrc;
    INT16U    *pdest;
#endif
#if OS_CRITICAL_METHOD == 3  
    OS_CPU_SR  cpu_sr = 0;
#endif

    if (OSIntNesting > 0) { 
        return (OS_ERR_QUERY_ISR);
    }
#if OS_ARG_CHK_EN > 0
    if (pevent == (OS_EVENT *)0) {   
        return (OS_ERR_PEVENT_NULL);
    }
    if (p_mutex_data == (OS_MUTEX_DATA *)0) {
        return (OS_ERR_PDATA_NULL);
    }
#endif
    if (pevent->OSEventType != OS_EVENT_TYPE_MUTEX) {  
        return (OS_ERR_EVENT_TYPE);
    }
    OS_ENTER_CRITICAL();

    //填充输入型参数p_mutex_data
    //天花板优先级
    p_mutex_data->OSMutexPIP  = (INT8U)(pevent->OSEventCnt >> 8);  
    //持有Mutex的任务的优先级
    p_mutex_data->OSOwnerPrio = (INT8U)(pevent->OSEventCnt & OS_MUTEX_KEEP_LOWER_8);

    如果占用mutex任务的优先级为255，表示该Mutex可用
    if (p_mutex_data->OSOwnerPrio == 0xFF) {
        p_mutex_data->OSValue = OS_TRUE; //可用
    } else {  
        p_mutex_data->OSValue = OS_FALSE; //不可用
    }

    //等待事件组
    p_mutex_data->OSEventGrp  = pevent->OSEventGrp; 
    //等待事件组的源地址
    psrc                      = &pevent->OSEventTbl[0];

    //等待事件的目的地址
    pdest                     = &p_mutex_data->OSEventTbl[0];

    //拷贝
    for (i = 0; i < OS_EVENT_TBL_SIZE; i++) {
        *pdest++ = *psrc++;
    }
    OS_EXIT_CRITICAL();
    return (OS_ERR_NONE);
}
#endif   
```

## 7. 还原任务的优先级函数OSMutex_RdyAtPrio()

这个函数在上面函数被调用过。

```static  void  OSMutex_RdyAtPrio (OS_TCB  *ptcb,
                                 INT8U    prio)
{
    // 将当前任务从就绪表中拿出，即不让当前任务为就绪态
    INT8U  y;
    y            =  ptcb->OSTCBY;          
    OSRdyTbl[y] &= (OS_PRIO)~ptcb->OSTCBBitX;
    if (OSRdyTbl[y] == 0u) {
        OSRdyGrp &= (OS_PRIO)~ptcb->OSTCBBitY;
    }
    //还原当前任务的优先级
    ptcb->OSTCBPrio         = prio;
    OSPrioCur               = prio; 

//优先级改变了，下面与优先级相关的参数也要做改变
#if OS_LOWEST_PRIO <= 63u
    ptcb->OSTCBY            = (INT8U)((INT8U)(prio >> 3u) & 0x07u);
    ptcb->OSTCBX            = (INT8U)(prio & 0x07u);
#else
    ptcb->OSTCBY            = (INT8U)((INT8U)(prio >> 4u) & 0x0Fu);
    ptcb->OSTCBX            = (INT8U) (prio & 0x0Fu);
#endif

//再将该任务在就绪表中标志位就绪态。因为优先级变了，那么在就绪表中对应的节点也改变了
    ptcb->OSTCBBitY         = (OS_PRIO)(1uL << ptcb->OSTCBY);
    ptcb->OSTCBBitX         = (OS_PRIO)(1uL << ptcb->OSTCBX);
    OSRdyGrp               |= ptcb->OSTCBBitY;             /* Make task ready at original priority     */
    OSRdyTbl[ptcb->OSTCBY] |= ptcb->OSTCBBitX;
    OSTCBPrioTbl[prio]      = ptcb;
}
#endif   
```