# os_mbox.c解析

[toc]

定位到uCOS-II/Source/os_mbox.c，该文件是消息邮箱管理的相关操作函数。

  任务与任务之间需要数据传递，那么为了适应传递的数据的不同类型，可以建立一个缓冲区(void*类型可以接收不同类型的数据)，然后以该缓冲区为介质来实现任务间的切换，这就是消息邮箱的数据传输原理。

  消息邮箱的具体实现是：将数据缓冲区的指针赋给事件控制块(OS_EVENT)的成员OSEventPtr(OSEventPtr是个void* 类型)，同时设置OSEventPtr中的用于表示事件类型的成员OSEventType为OS_EVENT_TYPE_MBOX。

定位到uCOS-II/Source/os_mbox.c，该文件是消息邮箱管理的相关操作函数。


## 1. 查看邮箱是否有需要的消息函数OSMboxAccept()
  OSMboxAccept()是非阻塞的，和OSMboxPend()函数不同(在下面解析)。OSMboxAccept()会从消息邮箱中试图取出消息，若没有消息可取，OSMboxAccept()函数并不挂起任务。若有消息可提取，则OSMboxAccept()函数提取消息完毕后会将该邮箱中存放消息的位置清空。因为该函数是非阻塞的，所以它允许在ISR中被调用。

```#if OS_MBOX_ACCEPT_EN > 0u
void  *OSMboxAccept (OS_EVENT *pevent)
{
    void      *pmsg;
#if OS_CRITICAL_METHOD == 3u 
    OS_CPU_SR  cpu_sr = 0u;
#endif

#if OS_ARG_CHK_EN > 0u
    if (pevent == (OS_EVENT *)0) {
        return ((void *)0);
    }
#endif
    if (pevent->OSEventType != OS_EVENT_TYPE_MBOX) { //pevent类型检查
        return ((void *)0);
    }
    OS_ENTER_CRITICAL();
    pmsg               = pevent->OSEventPtr;    //取出消息中的内容
    pevent->OSEventPtr = (void *)0;
    OS_EXIT_CRITICAL();     //取出后将其清空
    return (pmsg);   
}
#endif
```

## 2. 创建一个邮箱函数OSMboxCreate()

OSMboxCreate()函数用于建立并初始化一个邮箱信息，参数是消息指针，返回值是消息邮箱的指针。

```OS_EVENT  *OSMboxCreate (void *pmsg)
{
    OS_EVENT  *pevent;
#if OS_CRITICAL_METHOD == 3u
    OS_CPU_SR  cpu_sr = 0u;
#endif

#ifdef OS_SAFETY_CRITICAL_IEC61508
    if (OSSafetyCriticalStartFlag == OS_TRUE) {
        OS_SAFETY_CRITICAL_EXCEPTION();
        return ((OS_EVENT *)0);
    }
#endif

    if (OSIntNesting > 0u) {
        return ((OS_EVENT *)0);
    }
    OS_ENTER_CRITICAL();

    //取出空闲事件节点 
    pevent = OSEventFreeList;
    if (OSEventFreeList != (OS_EVENT *)0) {
        //全局变量OSEventFreeList指向下一个空闲事件节点
        OSEventFreeList = (OS_EVENT *)OSEventFreeList->OSEventPtr;
    }
    OS_EXIT_CRITICAL();
    //初始化该空闲事件节点为消息邮箱的相关设置
    if (pevent != (OS_EVENT *)0) {
        pevent->OSEventType    = OS_EVENT_TYPE_MBOX;
        pevent->OSEventCnt     = 0u;    //其实对mbox来说此参数没用
        pevent->OSEventPtr     = pmsg;
#if OS_EVENT_NAME_EN > 0u
        pevent->OSEventName    = (INT8U *)(void *)"?";
#endif
        OS_EventWaitListInit(pevent);   //定义在os_core.c中，置空该事件的等待队列
    }
    return (pevent); 
}

```

任务调用OSMboxCreate()时一般其参数msg为NULL，也可以事先定义一个邮箱，然后将该邮箱内的消息指针传递给OSMboxCreate()函数的msg，从而使得新建的邮箱从一开始就指代一个邮箱。

## 3. 删除邮箱函数OSMboxDel()
删除消息邮箱，因为其他任务可能处于等待获取该消息邮箱，所以在删除之前应该要安置好这些等待任务。

```#if OS_MBOX_DEL_EN > 0u
OS_EVENT  *OSMboxDel (OS_EVENT  *pevent,    //指定邮箱
                      INT8U      opt,       //删除操作选项
                      INT8U     *perr)      //输出型参数，用于指定出错信息
{
    BOOLEAN    tasks_waiting;
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
    if (pevent->OSEventType != OS_EVENT_TYPE_MBOX) {
        *perr = OS_ERR_EVENT_TYPE;
        return (pevent);
    }
    if (OSIntNesting > 0u) {
        *perr = OS_ERR_DEL_ISR;
        return (pevent);
    }
    OS_ENTER_CRITICAL();
    if (pevent->OSEventGrp != 0u) { //有任务在阻塞等待该MBox上的消息
        tasks_waiting = OS_TRUE;    //Yes
    } else {
        tasks_waiting = OS_FALSE;   //No
    }
    switch (opt) {
        case OS_DEL_NO_PEND:    //opt等于OS_DEL_NO_PEND表示无任务在等待才删除该Mbox
             if (tasks_waiting == OS_FALSE) {   //无任务等待
#if OS_EVENT_NAME_EN > 0u
                 pevent->OSEventName = (INT8U *)(void *)"?";
#endif
                 pevent->OSEventType = OS_EVENT_TYPE_UNUSED; //设置事件为空闲状态
                 pevent->OSEventPtr  = OSEventFreeList;      //OSEventFreeList原先是指向具体消息的，现指向下一个空闲事件节点
                 pevent->OSEventCnt  = 0u;                   //计数器，Mbox没用处
                 OSEventFreeList     = pevent;
                 OS_EXIT_CRITICAL();
                 *perr               = OS_ERR_NONE;
                 pevent_return       = (OS_EVENT *)0;
             } else {   //有任务等待，出错返回
                 OS_EXIT_CRITICAL();
                 *perr               = OS_ERR_TASK_WAITING;
                 pevent_return       = pevent;
             }
             break;

        case OS_DEL_ALWAYS:     //尽管有任务在等待还是要删除
             while (pevent->OSEventGrp != 0u) {  //有任务在等待，先逐一置为Rdy状态
                 (void)OS_EventTaskRdy(pevent, (void *)0, OS_STAT_MBOX, OS_STAT_PEND_ABORT);
             }
#if OS_EVENT_NAME_EN > 0u
             pevent->OSEventName    = (INT8U *)(void *)"?";
#endif
             //一样的删除操作
             pevent->OSEventType    = OS_EVENT_TYPE_UNUSED;
             pevent->OSEventPtr     = OSEventFreeList;
             pevent->OSEventCnt     = 0u;
             OSEventFreeList        = pevent; 
             OS_EXIT_CRITICAL();
             if (tasks_waiting == OS_TRUE) { 
                 OS_Sched();  //若系统已经在运行，发起调度
             }
             *perr         = OS_ERR_NONE;
             pevent_return = (OS_EVENT *)0;
             break;

        default:  //操作选项有误，出错返回
             OS_EXIT_CRITICAL();
             *perr         = OS_ERR_INVALID_OPT;
             pevent_return = pevent;
             break;
    }
    return (pevent_return);
}
#endif
```

## 4. 阻塞请求消息邮箱函数OSMboxPend()
  任务请求邮箱时调用OSMboxPend()函数，该函数是带阻塞的：查看邮箱内存放消息的指针OSEventPtr是否为NULL，若不为NULL则将邮箱中的消息指针返回给调用者，若为NULL则使任务进入挂起状态，并会引发调度。

```void  *OSMboxPend (OS_EVENT  *pevent,    //指定MBox
                   INT32U     timeout,   //超时时间设置
                   INT8U     *perr)
{
    void      *pmsg;
#if OS_CRITICAL_METHOD == 3u
    OS_CPU_SR  cpu_sr = 0u;
#endif

#ifdef OS_SAFETY_CRITICAL
    if (perr == (INT8U *)0) {
        OS_SAFETY_CRITICAL_EXCEPTION();
        return ((void *)0);
    }
#endif

#if OS_ARG_CHK_EN > 0u
    if (pevent == (OS_EVENT *)0) {
        *perr = OS_ERR_PEVENT_NULL;
        return ((void *)0);
    }
#endif
    if (pevent->OSEventType != OS_EVENT_TYPE_MBOX) {
        *perr = OS_ERR_EVENT_TYPE;
        return ((void *)0);
    }
    if (OSIntNesting > 0u) {
        *perr = OS_ERR_PEND_ISR;
        return ((void *)0);
    }
    if (OSLockNesting > 0u) {
        *perr = OS_ERR_PEND_LOCKED;
        return ((void *)0);
    }
    OS_ENTER_CRITICAL();
    pmsg = pevent->OSEventPtr;      //取出邮箱内的消息
    if (pmsg != (void *)0) {        //邮箱中的消息不为NULL
        pevent->OSEventPtr = (void *)0; //读取完毕后清空该消息指针
        OS_EXIT_CRITICAL();
        *perr = OS_ERR_NONE;
        return (pmsg);
    }

    //执行到这里说明邮箱内的消息为空，需要阻塞
    OSTCBCur->OSTCBStat     |= OS_STAT_MBOX;        //进入等待消息邮箱状态，表只能通过消息邮箱唤醒  
    OSTCBCur->OSTCBStatPend  = OS_STAT_PEND_OK;     //挂起
    OSTCBCur->OSTCBDly       = timeout;             //超时时间
    OS_EventTaskWait(pevent);                       //定义在os_core.c中，将自身添加到事件等待列表中
    OS_EXIT_CRITICAL();
    OS_Sched();                                     //重新调度，调度后会有一个优先级比当前优先级低的任务得到执行
                                                    //而当前任务在等待有任务向Mbox发消息
    OS_ENTER_CRITICAL();

    //能执行到这里，说明其他任务：
    //a. 调用了OSMboxPostOpt()释放该Mbox
    //b. 调用OSMboxDel()、OSMboxPendAbort()删除了该Mbox
    //c. 等待超时
    switch (OSTCBCur->OSTCBStatPend) {
        case OS_STAT_PEND_OK:   //有任务调用了OSMboxPostOpt进而唤醒当前任务
             pmsg =  OSTCBCur->OSTCBMsg;  //提取任务的消息指针
            *perr =  OS_ERR_NONE;
             break;

        case OS_STAT_PEND_ABORT:    //MBox被删除了
             pmsg = (void *)0;
            *perr =  OS_ERR_PEND_ABORT;
             break;

        case OS_STAT_PEND_TO:       //超时，不再等待
        default:
             OS_EventTaskRemove(OSTCBCur, pevent);  //定义在os_core.c中，将当前任务从event等待列表中清除
             pmsg = (void *)0;
            *perr =  OS_ERR_TIMEOUT; 
             break;
    }

    //设置任务状态
    OSTCBCur->OSTCBStat          =  OS_STAT_RDY; 
    OSTCBCur->OSTCBStatPend      =  OS_STAT_PEND_OK;
    OSTCBCur->OSTCBEventPtr      = (OS_EVENT  *)0;
#if (OS_EVENT_MULTI_EN > 0u)
    OSTCBCur->OSTCBEventMultiPtr = (OS_EVENT **)0;
#endif
    OSTCBCur->OSTCBMsg           = (void      *)0; 
    OS_EXIT_CRITICAL();
    return (pmsg);
}
```

在超时时间范围内收到消息后，任务是通过”OSTCBCur->OSTCBMsg”提取消息并继续执行的，为什么不是”pevent->OSEventPtr”提取？
这是因为多任务消息传递时可以将消息直接赋给各个任务的TCB的OSTCBMsg成员。

## 5. 唤醒等待消息邮箱的任务函数OSMboxPendAbort()

其实这个函数并非pend(获取)，而是类似post(释放)MBox，具体实现唤醒单个/所有等待任务。

```#if OS_MBOX_PEND_ABORT_EN > 0u
INT8U  OSMboxPendAbort (OS_EVENT  *pevent,
                        INT8U      opt,
                        INT8U     *perr)
{
    INT8U      nbr_tasks;       //用于记录有多少个任务在等待该事件(Mbox)
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
    if (pevent->OSEventType != OS_EVENT_TYPE_MBOX) {
        *perr = OS_ERR_EVENT_TYPE;
        return (0u);
    }
    OS_ENTER_CRITICAL();
    if (pevent->OSEventGrp != 0u) {  //有任务在等待
        nbr_tasks = 0u;
        switch (opt) {
            case OS_PEND_OPT_BROADCAST:  //广播，唤醒所有在等待的任务
                 while (pevent->OSEventGrp != 0u) {
                     (void)OS_EventTaskRdy(pevent, (void *)0, OS_STAT_MBOX, OS_STAT_PEND_ABORT);
                     nbr_tasks++;
                 }
                 break;

            case OS_PEND_OPT_NONE:      /只唤醒一个任务，即优先级最高的一个
            default:
                 (void)OS_EventTaskRdy(pevent, (void *)0, OS_STAT_MBOX, OS_STAT_PEND_ABORT);
                 nbr_tasks++;
                 break;
        }
        OS_EXIT_CRITICAL();
        OS_Sched();1            //调度
        *perr = OS_ERR_PEND_ABORT;
        return (nbr_tasks);
    }
    OS_EXIT_CRITICAL();
    *perr = OS_ERR_NONE;
}
#endif
```

## 6. 向消息邮箱发送消息函数OSMboxPost()
 
任务可以通过OSMboxPost()函数向目标消息邮箱发送消息，参数二为消息缓冲区的指针。

```#if OS_MBOX_POST_EN > 0u
INT8U  OSMboxPost (OS_EVENT  *pevent,
                   void      *pmsg)
{
#if OS_CRITICAL_METHOD == 3u
    OS_CPU_SR  cpu_sr = 0u;
#endif

#if OS_ARG_CHK_EN > 0u
    if (pevent == (OS_EVENT *)0) {
        return (OS_ERR_PEVENT_NULL);
    }
    if (pmsg == (void *)0) {
        return (OS_ERR_POST_NULL_PTR);
    }
#endif
    if (pevent->OSEventType != OS_EVENT_TYPE_MBOX) {
        return (OS_ERR_EVENT_TYPE);
    }
    OS_ENTER_CRITICAL();
    if (pevent->OSEventGrp != 0u) {  //有任务在等待

        //唤醒等待任务中优先级最高的任务，并将消息填充到该任务的TCB的OSTCBMsg成员中
        (void)OS_EventTaskRdy(pevent, pmsg, OS_STAT_MBOX, OS_STAT_PEND_OK);
        OS_EXIT_CRITICAL();
        OS_Sched();         //调度
        return (OS_ERR_NONE);
    }

    //若消息邮箱中的消息指针已经存有数据，出错返回
    if (pevent->OSEventPtr != (void *)0) {
        OS_EXIT_CRITICAL();
        return (OS_ERR_MBOX_FULL);
    }

    //没任务等待且消息邮箱中的消息指针不为空，将pmsg赋给消息邮箱的消息指针
    pevent->OSEventPtr = pmsg; 
    OS_EXIT_CRITICAL();
    return (OS_ERR_NONE);
}
#endif
```
这里需要注意，定义在OS_EventTaskRdy()的函数的具体实现并非将pmsg消息赋给消息邮箱的消息指针而是赋给最高优先级任务的TCB的OSTCBMsg成员，这就跟前面OSMboxPend()函数中提取消息操作”pmsg = OSTCBCur->OSTCBMsg”对应上了。

由此可见，uCOS-II为了效率，还可以将数据赋给即将被调度运行的目标任务的TCB的OSTCBMsg成员。

## 7. 向邮箱发送消息的另一函数OSMboxPostOpt()

OSMboxPostOpt()函数可以以广播的方式向MBox时间等待任务列表中的所有任务发送消息。

```#if OS_MBOX_POST_OPT_EN > 0u
INT8U  OSMboxPostOpt (OS_EVENT  *pevent,
                      void      *pmsg,
                      INT8U      opt)
{
#if OS_CRITICAL_METHOD == 3u
    OS_CPU_SR  cpu_sr = 0u;
#endif

#if OS_ARG_CHK_EN > 0u
    if (pevent == (OS_EVENT *)0) {
        return (OS_ERR_PEVENT_NULL);
    }
    if (pmsg == (void *)0) {
        return (OS_ERR_POST_NULL_PTR);
    }
#endif
    if (pevent->OSEventType != OS_EVENT_TYPE_MBOX) {
        return (OS_ERR_EVENT_TYPE);
    }
    OS_ENTER_CRITICAL();
    if (pevent->OSEventGrp != 0u) {
        if ((opt & OS_POST_OPT_BROADCAST) != 0x00u) { //含有OS_POST_OPT_BROADCAST操作选项
            while (pevent->OSEventGrp != 0u) { // 有任务在等待
                 //唤醒任务并将消息pmsg填充到该任务的TCB的OSTCBMsg中
                (void)OS_EventTaskRdy(pevent, pmsg, OS_STAT_MBOX, OS_STAT_PEND_OK);
            }
        } else {
            //唤醒单个任务，优先级最高的
            (void)OS_EventTaskRdy(pevent, pmsg, OS_STAT_MBOX, OS_STAT_PEND_OK);
        }
        OS_EXIT_CRITICAL();

        if ((opt & OS_POST_OPT_NO_SCHED) == 0u) { //为0表示没有包含OS_POST_OPT_NO_SCHED操作选项
            OS_Sched();         //需要调度
        }
        return (OS_ERR_NONE);
    }

    //若消息邮箱中的消息指针已经存有数据，出错返回
    if (pevent->OSEventPtr != (void *)0) { 
        OS_EXIT_CRITICAL();
        return (OS_ERR_MBOX_FULL);
    }

    //没任务等待且消息邮箱中的消息指针不为空，将pmsg赋给消息邮箱的消息指针
    pevent->OSEventPtr = pmsg;
    OS_EXIT_CRITICAL();
    return (OS_ERR_NONE);
}
#endif
```

## 8. 查询邮箱状态函数OSMboxQuery()
  
OSMboxQuery()可用于查看MBox的状态，其状态信息保存在函数的输入型参数p_mbox_data中，p_mbox_data为OS_MBOX_DATA类型的指针，OS_MBOX_DATA原型为：

```typedef struct os_mbox_data {
    void   *OSMsg;                          //消息邮箱的有效信息

    //任务等待列表，存放等待该MBox的所有任务
#if OS_LOWEST_PRIO <= 63
    INT8U   OSEventTbl[OS_EVENT_TBL_SIZE];
    INT8U   OSEventGrp;
#else
    INT16U  OSEventTbl[OS_EVENT_TBL_SIZE];
    INT16U  OSEventGrp; 
#endif
} OS_MBOX_DATA;

```

函数原型为：

```#if OS_MBOX_QUERY_EN > 0u
INT8U  OSMboxQuery (OS_EVENT      *pevent,
                    OS_MBOX_DATA  *p_mbox_data)
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
    if (p_mbox_data == (OS_MBOX_DATA *)0) {
        return (OS_ERR_PDATA_NULL);
    }
#endif
    if (pevent->OSEventType != OS_EVENT_TYPE_MBOX) {
        return (OS_ERR_EVENT_TYPE);
    }

    OS_ENTER_CRITICAL();
    p_mbox_data->OSEventGrp = pevent->OSEventGrp;

    //(等待任务)数组赋值，需要用for()语句逐一赋值
    psrc                    = &pevent->OSEventTbl[0];
    pdest                   = &p_mbox_data->OSEventTbl[0];
    for (i = 0u; i < OS_EVENT_TBL_SIZE; i++) {
        *pdest++ = *psrc++;
    }
    p_mbox_data->OSMsg = pevent->OSEventPtr; 
    OS_EXIT_CRITICAL();
    return (OS_ERR_NONE);
}
#endif
```
---