# os_sem.c 解析

[toc]

定位到uCOS-II/Source/os_sem.c，该文件是信号量的相关操作函数。

信号量适用于资源保护的场合，它和互斥型信号量Mutex一样，用于保护着某个共享资源，二者的差别是：Mutex是二值的(0/1)，其初始值为1，某任务要操作共享资源，需要获取信号量，获取后信号量计数器为0，那么下一个任务来获取该Mutex将获取不到；而信号量Semaphore的初始值(信号量计数器)可以为大于1的数，假设为3，，那么任务A要使用该资源时，获取信号量后信号量值为2，同理，被任务B获取后信号量值为1，任务C获取后信号量值为0，那么再下一个任务来获取时就将获取不到信号量了。

## 1. 非阻塞的获取一个信号量函数OSSemAccept()
OSSemAccept()用于检测信号量是否可用，若资源不可用，调用此函数不会使得所在任务被挂起。

```#if OS_SEM_ACCEPT_EN > 0u               //定义OSSemAccept()函数使能宏
INT16U  OSSemAccept (OS_EVENT *pevent)  //pevent指向需要保护的共享资源的信号量
{
    INT16U     cnt;
#if OS_CRITICAL_METHOD == 3u            //信号量中的值
    OS_CPU_SR  cpu_sr = 0u;
#endif

#if OS_ARG_CHK_EN > 0u                  //参数检测使能宏
    if (pevent == (OS_EVENT *)0) { 
        return (0u);
    }
#endif
    if (pevent->OSEventType != OS_EVENT_TYPE_SEM) { 
        return (0u);
    }
    OS_ENTER_CRITICAL();
    cnt = pevent->OSEventCnt;           //取出信号量的值
    if (cnt > 0u) {                     //大于0表示信号量还可以使用
        pevent->OSEventCnt--;           //自减表示使用了该信号量
    }
    OS_EXIT_CRITICAL();
    return (cnt);                       //返回值cnt大于0表示获取信号量成功，反之获取失败
}
#endif
```

## 2. 创建信号量函数OSSemCreate()
OSSemCreate()用于创建并初始化一个信号量。

```OS_EVENT  *OSSemCreate (INT16U cnt)     //cnt为信号量的初始值
{
    OS_EVENT  *pevent;
#if OS_CRITICAL_METHOD == 3u
    OS_CPU_SR  cpu_sr = 0u;
#endif

#ifdef OS_SAFETY_CRITICAL_IEC61508      //系统安全相关，不管
    if (OSSafetyCriticalStartFlag == OS_TRUE) {
        OS_SAFETY_CRITICAL_EXCEPTION();
        return ((OS_EVENT *)0);
    }
#endif

    if (OSIntNesting > 0u) { 
        return ((OS_EVENT *)0);
    }
    OS_ENTER_CRITICAL();
    pevent = OSEventFreeList;               //pevent指向空闲事件链表
    if (OSEventFreeList != (OS_EVENT *)0) { //如果有空余事件管理块 
        //空闲事件控制链表指向下一个空闲事件控制块  
        OSEventFreeList = (OS_EVENT *)OSEventFreeList->OSEventPtr;
    }
    OS_EXIT_CRITICAL();
    if (pevent != (OS_EVENT *)0) {  //解引用前先判断指针是否有效
        //初始化该event(信号量)的相关参数
        pevent->OSEventType    = OS_EVENT_TYPE_SEM;
        pevent->OSEventCnt     = cnt;
        pevent->OSEventPtr     = (void *)0; //OSEventPtr初始值为空，等到某任务获取该event后，OSEventPtr指向该任务的TCB
#if OS_EVENT_NAME_EN > 0u
        pevent->OSEventName    = (INT8U *)(void *)"?";
#endif
        OS_EventWaitListInit(pevent);       //定义在os_core.c中，实现清空该event的等待列表OSEventTbl和等待组OSEventGrp
    }
    return (pevent);
}
```

## 3. 删除信号量函数OSSemDel()
OSSemDel()函数用于删除一个信号量，因为可能存在其他多个任务在等待这个信号量，所以注意，删除之前对这些等待任务执行相关操作。

```#if OS_SEM_DEL_EN > 0u                  //允许定义OSSemDel()函数
OS_EVENT  *OSSemDel (OS_EVENT  *pevent, //指向待删除的信号量
                     INT8U      opt,    //删除选项：OS_DEL_NO_PEND/OS_DEL_ALWAYS
                     INT8U     *perr)   //输出型参数，用于存放出错信息
{
    BOOLEAN    tasks_waiting;           //Bool型变量，用于表示是否有任务在等待该事件
    OS_EVENT  *pevent_return;
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
    if (pevent->OSEventType != OS_EVENT_TYPE_SEM) {
        *perr = OS_ERR_EVENT_TYPE;
        return (pevent);
    }
    if (OSIntNesting > 0u) {
        *perr = OS_ERR_DEL_ISR; 
        return (pevent);
    }
    OS_ENTER_CRITICAL();

    //OSEventGrp不等于0表示当前有任务在等待该事件
    if (pevent->OSEventGrp != 0u) {
        tasks_waiting = OS_TRUE;    //Yes
    } else {
        tasks_waiting = OS_FALSE;   //No
    }

    switch (opt) {
        //opt等于OS_DEL_NO_PEND表示若有任务在等待就不删除
        //opt等于OS_DEL_ALWAYS表示不管有无任务等待都删除该event
        case OS_DEL_NO_PEND:
             if (tasks_waiting == OS_FALSE) {   //无任务等待
#if OS_EVENT_NAME_EN > 0u
                 pevent->OSEventName    = (INT8U *)(void *)"?";
#endif
                 pevent->OSEventType    = OS_EVENT_TYPE_UNUSED;  //设置该event为未使用状态
                 pevent->OSEventPtr     = OSEventFreeList;       //信号量对应的指针设置为空闲块链接表  
                 pevent->OSEventCnt     = 0u;                    //信号量初始值为0
                 OSEventFreeList        = pevent;                //空线块链接表等于当前事件指针  
                 OS_EXIT_CRITICAL();
                 *perr                  = OS_ERR_NONE;
                 pevent_return          = (OS_EVENT *)0;         //返回NULL
             } else {                   //有任务在等待
                 OS_EXIT_CRITICAL();
                 *perr                  = OS_ERR_TASK_WAITING;   //返回错误(有一个或一个以上的任务在等待信号量) 
                 pevent_return          = pevent;
             }
             break;

        case OS_DEL_ALWAYS:
             //OSEventGrp不为0表示有任务在等待该信号量，那么挨个清除这个在等待的任务的等待标记，
             //即将它们设置Rdy状态
             while (pevent->OSEventGrp != 0u) {
                 (void)OS_EventTaskRdy(pevent, (void *)0, OS_STAT_SEM, OS_STAT_PEND_ABORT);
             }
#if OS_EVENT_NAME_EN > 0u
             pevent->OSEventName    = (INT8U *)(void *)"?";
#endif
             pevent->OSEventType    = OS_EVENT_TYPE_UNUSED;
             pevent->OSEventPtr     = OSEventFreeList;
             pevent->OSEventCnt     = 0u;
             OSEventFreeList        = pevent;
             OS_EXIT_CRITICAL();

             //若系统正在运行则进行调度
             if (tasks_waiting == OS_TRUE) {
                 OS_Sched(); 
             }
             *perr                  = OS_ERR_NONE;
             pevent_return          = (OS_EVENT *)0; 
             break;

        default:  //opt输入有误
             OS_EXIT_CRITICAL();
             *perr                  = OS_ERR_INVALID_OPT;
             pevent_return          = pevent;
             break;
    }
    return (pevent_return);
}
#endif
```

## 4. 阻塞的获取一个信号量函数OSSemPend ()
任务在试图取得共享资源的使用权时，通过此函数去获取保护该资源的信号量，若成功获取信号量(获取前的信号量计数器大于0)则返回，反之陷入等待状态，直到有其他任务释放了该信号量，或者超时，或者该信号量被其他任务删除而被唤醒。

```void  OSSemPend (OS_EVENT  *pevent,     //指向信号量指针
                 INT32U     timeout,    //该函数在获取不到信号时的阻塞超时时间，单位为systick
                 INT8U     *perr)       //输入型参数，表示出错原因
{
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
    if (pevent->OSEventType != OS_EVENT_TYPE_SEM) {
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
    if (pevent->OSEventCnt > 0u) { //信号量计数器>0表示信号量还可以使用
        pevent->OSEventCnt--;       //自减
        OS_EXIT_CRITICAL();
        *perr = OS_ERR_NONE;
        return;                     //获取成功，返回
    }

    //执行到这里说明信号量已经被其他任务取完，要陷入等待信号量的阻塞状态
    OSTCBCur->OSTCBStat     |= OS_STAT_SEM;     //将任务状态置为等待信号量状态
    OSTCBCur->OSTCBStatPend  = OS_STAT_PEND_OK; //挂起
    OSTCBCur->OSTCBDly       = timeout;         //设置等待超时时间   
    OS_EventTaskWait(pevent);                   //定义在os_core.c中，调用此函数使得当前任务陷入等待：
                                                //将当前任务添加到pevent指向的event等待链表中
    OS_EXIT_CRITICAL();
    OS_Sched();   //调度
    OS_ENTER_CRITICAL();

    //能执行到这里说明当前任务从挂起状态中醒来了
    switch (OSTCBCur->OSTCBStatPend) {      //正确等待目标信号量的到来
        case OS_STAT_PEND_OK:
             *perr = OS_ERR_NONE;       //正常返回
             break;

        case OS_STAT_PEND_ABORT:            //别的任务已经将目标信号量删除而唤醒本任务
             *perr = OS_ERR_PEND_ABORT;  
             break;

        case OS_STAT_PEND_TO:           //等待超时
        default:
             OS_EventTaskRemove(OSTCBCur, pevent);  //删除当前任务在该信号量中等待队列中等待标记
             *perr = OS_ERR_TIMEOUT;                  /* Indicate that we didn't get event within TO   */
             break;
    }

    //设置相关状态量
    OSTCBCur->OSTCBStat          =  OS_STAT_RDY;   
    OSTCBCur->OSTCBStatPend      =  OS_STAT_PEND_OK;
    OSTCBCur->OSTCBEventPtr      = (OS_EVENT  *)0;
#if (OS_EVENT_MULTI_EN > 0u)    //OS_EVENT_MULTI_EN表示可以等待多个事件
    OSTCBCur->OSTCBEventMultiPtr = (OS_EVENT **)0;
#endif
    OS_EXIT_CRITICAL();
}
```

## 5. 以删除信号量的方式唤醒等待任务的函数OSSemPendAbort()
正常情况下调用OSSempost()函数(该函数分析在下面)来释放一个信号量以通知其它在正在等待该信号量的任务得以继续执行，但是在非正常情况下，可以调用此函数实现废除信号量，同时同样让所有等待该信号的任务被唤醒后继续执行。

```#if OS_SEM_PEND_ABORT_EN > 0u
INT8U  OSSemPendAbort (OS_EVENT  *pevent,   //指向信号量指针
                       INT8U      opt,      //操作选项
                       INT8U     *perr)
{
    INT8U      nbr_tasks;
#if OS_CRITICAL_METHOD == 3u
    OS_CPU_SR  cpu_sr = 0u;
#endif

#ifdef OS_SAFETY_CRITICAL
    if (perr == (INT8U *)0) {
        OS_SAFETY_CRITICAL_EXCEPTION();
        return (0u);
    }
#endif

#if OS_ARG_CHK_EN > 0u
    if (pevent == (OS_EVENT *)0) {
        *perr = OS_ERR_PEVENT_NULL;
        return (0u);
    }
#endif
    if (pevent->OSEventType != OS_EVENT_TYPE_SEM) {
        *perr = OS_ERR_EVENT_TYPE;
        return (0u);
    }
    OS_ENTER_CRITICAL();
    if (pevent->OSEventGrp != 0u) { //OSEventGrp不等于0说明有任务在等待该信号量
        nbr_tasks = 0u;
        switch (opt) {
            case OS_PEND_OPT_BROADCAST: //BROADCAST意为广播，即将所有等待惹怒都设置为Rdy状态使其不再等待
                 while (pevent->OSEventGrp != 0u) {
                     (void)OS_EventTaskRdy(pevent, (void *)0, OS_STAT_SEM, OS_STAT_PEND_ABORT);
                     nbr_tasks++;
                 }
                 break;

            case OS_PEND_OPT_NONE:  //只唤醒一个在等待本信号量的任务，即在等待任务群中优先级最高的一个(HTP)
            default:
                  //OS_EventTaskRdy()定义在os_core.c中，用户唤醒pevent中的等待任务列表中优先级最高的任务
                 (void)OS_EventTaskRdy(pevent, (void *)0, OS_STAT_SEM, OS_STAT_PEND_ABORT);
                 nbr_tasks++;
                 break;
        }
        OS_EXIT_CRITICAL();
        OS_Sched();             //重新调度
        *perr = OS_ERR_PEND_ABORT;
        return (nbr_tasks);
    }

    //没任务在等待该信号量，啥都不做
    OS_EXIT_CRITICAL();
    *perr = OS_ERR_NONE;
    return (0u);
}
#endif

```

## 6. 释放信号量函数OSSemPost()
OSSemPost()函数用于释放信号量，唤醒在等待该信号量的任务队列中优先级最高的任务。

```INT8U  OSSemPost (OS_EVENT *pevent)
{
#if OS_CRITICAL_METHOD == 3u
    OS_CPU_SR  cpu_sr = 0u;
#endif

#if OS_ARG_CHK_EN > 0u
    if (pevent == (OS_EVENT *)0) {
        return (OS_ERR_PEVENT_NULL);
    }
#endif
    if (pevent->OSEventType != OS_EVENT_TYPE_SEM) {
        return (OS_ERR_EVENT_TYPE);
    }
    OS_ENTER_CRITICAL();
    if (pevent->OSEventGrp != 0u) { //有任务在等待

         //唤醒优先级最高的等待任务
        (void)OS_EventTaskRdy(pevent, (void *)0, OS_STAT_SEM, OS_STAT_PEND_OK);
        OS_EXIT_CRITICAL();
        OS_Sched();                 //重新调度
        return (OS_ERR_NONE);
    }

    //执行到这里，说明并没有任务在等待，那么释放信号量的操作很简单，因为获取信号量是自减一操作，那么释放则自加一
    if (pevent->OSEventCnt < 65535u) {
        pevent->OSEventCnt++; 
        OS_EXIT_CRITICAL();
        return (OS_ERR_NONE);
    }
    OS_EXIT_CRITICAL();                               /* Semaphore value has reached its maximum       */
    return (OS_ERR_SEM_OVF);
}
```

提两个问题：
(1) 为什么OSSemPost()函数唤醒的是任务等待队列中优先级最高的一个而OSSemPendAbort的操作选项中有唤醒全部？
因为正常情况下释放一个信号量只会被一个任务获取到，该任务自然是优先级最高的一个，那么假设唤醒了全部等待的任务也没用。而OSSemPendAbort()有广播唤醒任务的选项是因为信号量已经被Abort了，所以要告诉所有等待任务不要继续等待了。

(2) 为什么当有任务在等待该信号量的时候，释放信号量操作cnt不需要自加一？
因为其他任务在获取信号量时若获取不到时只是陷入等待状态而没有执行cnt自减一操作。

## 7. 获取一个信号量的信息函数OSSemQuery()
OSSemQuery()函数用于获取信号量的信息，存储于OS_SEM_DATA结构体中。

```#if OS_SEM_QUERY_EN > 0u
INT8U  OSSemQuery (OS_EVENT     *pevent,
                   OS_SEM_DATA  *p_sem_data)    //输入型参数，用于存放信号量信息
{
    INT8U       i;
    OS_PRIO    *psrc;
    OS_PRIO    *pdest;
#if OS_CRITICAL_METHOD == 3u
    OS_CPU_SR   cpu_sr = 0u;
#endif

#if OS_ARG_CHK_EN > 0u
    if (pevent == (OS_EVENT *)0) {
        return (OS_ERR_PEVENT_NULL);
    }
    if (p_sem_data == (OS_SEM_DATA *)0) {
        return (OS_ERR_PDATA_NULL);
    }
#endif
    if (pevent->OSEventType != OS_EVENT_TYPE_SEM) {
        return (OS_ERR_EVENT_TYPE);
    }
    OS_ENTER_CRITICAL();
    p_sem_data->OSEventGrp = pevent->OSEventGrp; 

    //数组不能直接赋值，需要对所有成员逐一赋值
    psrc                   = &pevent->OSEventTbl[0];
    pdest                  = &p_sem_data->OSEventTbl[0];
    for (i = 0u; i < OS_EVENT_TBL_SIZE; i++) {
        *pdest++ = *psrc++;
    }
    p_sem_data->OSCnt = pevent->OSEventCnt;                /* Get semaphore count                      */
    OS_EXIT_CRITICAL();
    return (OS_ERR_NONE);
}
#endif 

```

## 8. 设置信号量的计数值函数OSSemSet()
信号量的计数值在创建信号量时候OSSemCreate()的初始化操作中已经确定，在程序运行期间还可以通过OSSemSet()函数改变其计数值。

```#if OS_SEM_SET_EN > 0u
void  OSSemSet (OS_EVENT  *pevent,
                INT16U     cnt,     //
                INT8U     *perr)
{
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
    if (pevent->OSEventType != OS_EVENT_TYPE_SEM) {
        *perr = OS_ERR_EVENT_TYPE;
        return;
    }

    OS_ENTER_CRITICAL();
    *perr = OS_ERR_NONE;
    if (pevent->OSEventCnt > 0u) {  //信号量还没被获取完，直接修改信号量计数值
        pevent->OSEventCnt = cnt; 
    } else {    //信号量已经被获取完
        if (pevent->OSEventGrp == 0u) { //没有任务在等待，直接修改
            pevent->OSEventCnt = cnt;
        } else {    //信号量被获取万里且当前还有任务在等待获取，这时候不可直接设置计数值，否则会使得正在等待信号量的任务
                    //被唤醒，扰乱程序执行逻辑
            *perr              = OS_ERR_TASK_WAITING;
        }
    }
    OS_EXIT_CRITICAL();
}
#endif
```
---