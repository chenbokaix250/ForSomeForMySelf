# os_task.c的解析


定位到uCOS-II/Source/os_task.c，该文件是任务的相关操作：

1. 修改任务优先级函数OSTaskChangePrio()
OSTaskChangePrio()适用于用户动态改变一个任务的优先级，但新的优先级必须符合要求。

```
#if OS_TASK_CHANGE_PRIO_EN > 0u
INT8U  OSTaskChangePrio (INT8U  oldprio, INT8U  newprio)
{
#if (OS_EVENT_EN)               /* 事件控制块配置宏 */
    OS_EVENT  *pevent;
#if (OS_EVENT_MULTI_EN > 0u)    /* 多事件控制块配置宏 */
    OS_EVENT **pevents;
#endif
#endif

    OS_TCB    *ptcb;
    INT8U      y_new;
    INT8U      x_new;
    INT8U      y_old;
    OS_PRIO    bity_new;
    OS_PRIO    bitx_new;
    OS_PRIO    bity_old;
    OS_PRIO    bitx_old;

#if OS_CRITICAL_METHOD == 3u    
    OS_CPU_SR  cpu_sr = 0u;     //为CPU状态寄存器分配存储器
#endif

#if OS_ARG_CHK_EN > 0u          //允许参数检查

    //旧优先级数值不合法
    if (oldprio >= OS_LOWEST_PRIO) {
        if (oldprio != OS_PRIO_SELF) {
            return (OS_ERR_PRIO_INVALID);
        }
    }

    //新优先级不合法
    if (newprio >= OS_LOWEST_PRIO) {
        return (OS_ERR_PRIO_INVALID);
    }
#endif
    OS_ENTER_CRITICAL();            //进入临界区
    if (OSTCBPrioTbl[newprio] != (OS_TCB *)0) { //不等于0说明已经存在优先级跟新优先级一样的任务了
        OS_EXIT_CRITICAL();
        return (OS_ERR_PRIO_EXIST);
    }

    //要改变优先级的任务是任务自己本身
    if (oldprio == OS_PRIO_SELF) { //OS_PRIO_SELF虽为0xff，但它指代任务自己
        oldprio = OSTCBCur->OSTCBPrio;  
    }

    //获取旧的优先级的任务的TCB
    ptcb = OSTCBPrioTbl[oldprio];

    //旧优先级的任务的TCB为空
    if (ptcb == (OS_TCB *)0) {
        OS_EXIT_CRITICAL(); 
        return (OS_ERR_PRIO);
    }

    //旧优先级的任务的TCB已经被保留/占领
    if (ptcb == OS_TCB_RESERVED) {
        OS_EXIT_CRITICAL();
        return (OS_ERR_TASK_NOT_EXIST);
    }
#if OS_LOWEST_PRIO <= 63u
    y_new                 = (INT8U)(newprio >> 3u);     //通过优先级数值得到优先级组，即OSRdyTbl[]的下标Y
    x_new                 = (INT8U)(newprio & 0x07u);   //通过优先级数值得到OSRdyTbl[Y]成员的具体哪一位X
#else
    y_new                 = (INT8U)((INT8U)(newprio >> 4u) & 0x0Fu);
    x_new                 = (INT8U)(newprio & 0x0Fu);
#endif

    bity_new              = (OS_PRIO)(1uL << y_new);    //bity_new和bitx_new目的方便在就绪表中登记就绪
    bitx_new              = (OS_PRIO)(1uL << x_new);    //两个数值替代了稍微老点的版本的OSMapTbl[]表格

    OSTCBPrioTbl[oldprio] = (OS_TCB *)0;    /* 旧优先级的TCB不再使用，置空 */

    /* 将任务放在newprio指定的TCB中 */
    OSTCBPrioTbl[newprio] =  ptcb; 

    /* 更改任务的优先级相关的参数 */
    y_old                 =  ptcb->OSTCBY;
    bity_old              =  ptcb->OSTCBBitY;
    bitx_old              =  ptcb->OSTCBBitX;
    if ((OSRdyTbl[y_old] &   bitx_old) != 0u) { //若旧优先级的任务为就绪态
         OSRdyTbl[y_old] &= (OS_PRIO)~bitx_old;    //设置旧优先级的任务为非就绪态。(这步很重要，因为就旧任务的TCB已经为空了，
                                                //若不更改为非就绪态，那么它将会得到系统的调度，一旦被调度就运行出错了)
         if (OSRdyTbl[y_old] == 0u) {           //设置旧优先级的任务的任务组
             OSRdyGrp &= (OS_PRIO)~bity_old;
         }

         //既然旧优先级的任务原先就处于就绪态，那么更改完优先级后还是还原其为就绪态
         OSRdyGrp        |= bity_new;                       /* Make new priority ready to run          */
         OSRdyTbl[y_new] |= bitx_new;
    }

#if (OS_EVENT_EN)           /事件控制使能
    pevent = ptcb->OSTCBEventPtr;
    if (pevent != (OS_EVENT *)0) {  //若pevent等于0说明原优先级的任务跟event没有关联，即没有等待信号量、Mutex那些
                                    //反之，将旧优先级的任务的pevent迁移到新优先级的任务的pevent
        //清空
        pevent->OSEventTbl[y_old] &= (OS_PRIO)~bitx_old;    /* Remove old task prio from wait list     */
        if (pevent->OSEventTbl[y_old] == 0u) {
            pevent->OSEventGrp    &= (OS_PRIO)~bity_old;
        }

        //迁移
        pevent->OSEventGrp        |= bity_new;              /* Add    new task prio to   wait list     */
        pevent->OSEventTbl[y_new] |= bitx_new;
    }
#if (OS_EVENT_MULTI_EN > 0u)
    //一个任务可以等待多个事件，将这些事件放在一起，用OSTCBEventMultiPtr指向它们
    if (ptcb->OSTCBEventMultiPtr != (OS_EVENT **)0) {
        pevents =  ptcb->OSTCBEventMultiPtr;
        pevent  = *pevents;
        while (pevent != (OS_EVENT *)0) {
            pevent->OSEventTbl[y_old] &= (OS_PRIO)~bitx_old;   /* Remove old task prio from wait lists */
            if (pevent->OSEventTbl[y_old] == 0u) {
                pevent->OSEventGrp    &= (OS_PRIO)~bity_old;
            }
            pevent->OSEventGrp        |= bity_new;          /* Add    new task prio to   wait lists    */
            pevent->OSEventTbl[y_new] |= bitx_new;
            pevents++;
            pevent                     = *pevents;
        }
    }
#endif
#endif
    ptcb->OSTCBPrio = newprio;                              /* Set new task priority                   */

    //更新任务的TCB中与优先级相关的就绪表坐标参数
    ptcb->OSTCBY    = y_new;
    ptcb->OSTCBX    = x_new;
    ptcb->OSTCBBitY = bity_new;
    ptcb->OSTCBBitX = bitx_new;
    OS_EXIT_CRITICAL();
    if (OSRunning == OS_TRUE) {
        OS_Sched();    /* 优先级发生改变，自然需要重新调度 */
    }
    return (OS_ERR_NONE);
}
#endif
```

2. 创建任务函数OSTaskCreate()uCOS-II支持动态创建和静态创建任务：
(1) 静态创建：在应用程序调用OSStart()之前创建好所有任务，OSStart()函数将全局变量OSRunning置一后系统开始调度
(2) 动态创建：在OSStart()之后创建任务
一般我们使用的是静态创建任务的方式。uCOS-II是一款RTOS，为保证实时性，不可在ISR中创建任务。
uCOS-II是通过任务控制块TCB来管理任务的，所以创建一个任务的工作实质上是创建一个TCB，并通过TCB将任务代码和任务堆栈关联起来形成一个完整的任务。当然还要将被创建的任务为就绪态并引发一次调度。

```
#if OS_TASK_CREATE_EN > 0u
INT8U  OSTaskCreate (void   (*task)(void *p_arg),   //指向任务代码
                     void    *p_arg,                //传递给任务代码的参数
                     OS_STK  *ptos,                 //指向任务堆栈的栈顶
                     INT8U    prio)                 //任务的优先级
{
    OS_STK     *psp;
    INT8U       err;
#if OS_CRITICAL_METHOD == 3u 
    OS_CPU_SR   cpu_sr = 0u;
#endif

#ifdef OS_SAFETY_CRITICAL_IEC61508          //IEC61508是标准，主要与风险和安全相关，不细究
    if (OSSafetyCriticalStartFlag == OS_TRUE) {
        OS_SAFETY_CRITICAL_EXCEPTION();
        return (OS_ERR_ILLEGAL_CREATE_RUN_TIME);
    }
#endif

#if OS_ARG_CHK_EN > 0u          //参数合法性判断使能
    if (prio > OS_LOWEST_PRIO) {
        return (OS_ERR_PRIO_INVALID);
    }
#endif
    OS_ENTER_CRITICAL();
    if (OSIntNesting > 0u) { //不可在中断ISR中创建任务
        OS_EXIT_CRITICAL();
        return (OS_ERR_TASK_CREATE_ISR);
    }
    if (OSTCBPrioTbl[prio] == (OS_TCB *)0) { //不等于0表示已经存在任务，其优先级与要创建的任务的优先级一致。
                                             //等于0说明不存在
        OSTCBPrioTbl[prio] = OS_TCB_RESERVED; //先RESERVED任务控制块，RESERVED即占领

        //占领了位置了，下来可以放心操作该任务的相关设置
        OS_EXIT_CRITICAL();                          //进入临界区
        psp = OSTaskStkInit(task, p_arg, ptos, 0u);  //初始化栈
        err = OS_TCBInit(prio, psp, (OS_STK *)0, 0u, 0u, (void *)0, 0u);  //初始化该任务的TCB
        if (err == OS_ERR_NONE) {
            if (OSRunning == OS_TRUE) { //如果os已经在运行了，引发调度
                OS_Sched();
            }   //如果os还没运行呢?这里并没有这个else。不必着急，等下APP调用OSStart()时候会开启调度，这是系统的首次调度
        } else {        //创建任务失败，让出占领TCB的位置
            OS_ENTER_CRITICAL();
            OSTCBPrioTbl[prio] = (OS_TCB *)0; 
            OS_EXIT_CRITICAL();
        }
        return (err);
    }
    OS_EXIT_CRITICAL();
    return (OS_ERR_PRIO_EXIST);
}
#endif
```

3. 创建任务函数OSTaskCreateExt()OSTaskCreateExt()函数是OSTaskCreate()的扩展，并提供了一些附加功能。用OSTaskCreateExt()来创建任务会更灵活，但是会增加一些额外的开销。

```#if OS_TASK_CREATE_EXT_EN > 0u
INT8U  OSTaskCreateExt (void   (*task)(void *p_arg), //指向任务代码
                        void    *p_arg,              //传递给任务代码的参数
                        OS_STK  *ptos,               //指向任务堆栈的栈顶
                        INT8U    prio,               //任务的优先级
                        INT16U   id,                 //任务的id
                        OS_STK  *pbos,               //指向任务堆栈的栈底
                        INT32U   stk_size,           //任务堆栈的大小
                        void    *pext,               //附加的数据
                        INT16U   opt)                //用于设定操作选项
{
    OS_STK     *psp;
    INT8U       err;
#if OS_CRITICAL_METHOD == 3u                 /* Allocate storage for CPU status register               */
    OS_CPU_SR   cpu_sr = 0u;
#endif

#ifdef OS_SAFETY_CRITICAL_IEC61508
    if (OSSafetyCriticalStartFlag == OS_TRUE) {
        OS_SAFETY_CRITICAL_EXCEPTION();
        return (OS_ERR_ILLEGAL_CREATE_RUN_TIME);
    }
#endif

#if OS_ARG_CHK_EN > 0u
    if (prio > OS_LOWEST_PRIO) {             /* Make sure priority is within allowable range           */
        return (OS_ERR_PRIO_INVALID);
    }
#endif
    OS_ENTER_CRITICAL();
    if (OSIntNesting > 0u) {                 /* Make sure we don't create the task from within an ISR  */
        OS_EXIT_CRITICAL();
        return (OS_ERR_TASK_CREATE_ISR);
    }
    if (OSTCBPrioTbl[prio] == (OS_TCB *)0) { /* Make sure task doesn't already exist at this priority  */
        OSTCBPrioTbl[prio] = OS_TCB_RESERVED;/* Reserve the priority to prevent others from doing ...  */
                                             /* ... the same thing until task is created.              */
        OS_EXIT_CRITICAL();

#if (OS_TASK_STAT_STK_CHK_EN > 0u)
        OS_TaskStkClr(pbos, stk_size, opt);                    /* Clear the task stack (if needed)     */
#endif

        psp = OSTaskStkInit(task, p_arg, ptos, opt);           /* Initialize the task's stack          */
        err = OS_TCBInit(prio, psp, pbos, id, stk_size, pext, opt);  /* 在前面的OSTaskCreate()调用此函数时候，最后5个参数都为0 */
        if (err == OS_ERR_NONE) {
            if (OSRunning == OS_TRUE) {                        /* Find HPT if multitasking has started */
                OS_Sched();
            }
        } else {
            OS_ENTER_CRITICAL();
            OSTCBPrioTbl[prio] = (OS_TCB *)0;                  /* Make this priority avail. to others  */
            OS_EXIT_CRITICAL();
        }
        return (err);
    }
    OS_EXIT_CRITICAL();
    return (OS_ERR_PRIO_EXIST);
}
#endif
```

一般来说，任务可在调用OSStart()启动任务调度之前创建，也可以在执行的任务中创建，但是uCOS-II规定，在调用启动任务函数OSStart()之前，必须至少创建了一个任务，因此用户习惯上在OSStart()之前创建一个任务，并赋予最高优先级别，从而使其为起始任务，然后在此任务中创建其他任务。若要使用系统的统计任务，统计任务的初始化函数也必须在这个起始任务中调用。

4. 删除任务函数OSTaskDel()删除任务的具体做法是，首先将该任务的任务控制块从任务控制块链表中删除，并归还空任务控制块，然后在任务就绪表中将该任务的就绪状态置为0，即非就绪态，那么它就不能被系统调度了：

```
#if OS_TASK_DEL_EN > 0u
INT8U  OSTaskDel (INT8U prio)
{
#if (OS_FLAG_EN > 0u) && (OS_MAX_FLAGS > 0u)
    OS_FLAG_NODE *pnode;
#endif
    OS_TCB       *ptcb;
#if OS_CRITICAL_METHOD == 3u                            /* Allocate storage for CPU status register    */
    OS_CPU_SR     cpu_sr = 0u;
#endif

    if (OSIntNesting > 0u) {                            /* See if trying to delete from ISR            */
        return (OS_ERR_TASK_DEL_ISR);
    }
    if (prio == OS_TASK_IDLE_PRIO) {   /* 不能删除空闲任务 */
        return (OS_ERR_TASK_DEL_IDLE);
    }
#if OS_ARG_CHK_EN > 0u
    if (prio >= OS_LOWEST_PRIO) {                       /* Task priority valid ?                       */
        if (prio != OS_PRIO_SELF) {
            return (OS_ERR_PRIO_INVALID);
        }
    }
#endif

    OS_ENTER_CRITICAL();
    if (prio == OS_PRIO_SELF) {  /* OS_PRIO_SELF指代要删除的是任务自己 */
        prio = OSTCBCur->OSTCBPrio;    /* 那么更改prio为任务自身的优先级 */
    }
    ptcb = OSTCBPrioTbl[prio];   /* 获得要删除的任务的TCB，可能是其他任务，可能是自己 */
    if (ptcb == (OS_TCB *)0) {   /* 任务不存在 */
        OS_EXIT_CRITICAL();
        return (OS_ERR_TASK_NOT_EXIST);
    }
    if (ptcb == OS_TCB_RESERVED) { /* 等于RESERVED表示该任务已经被占领预定了，被占领的任务控制块表示该任务为半成品 */
        OS_EXIT_CRITICAL();
        return (OS_ERR_TASK_DEL);
    }

    OSRdyTbl[ptcb->OSTCBY] &= (OS_PRIO)~ptcb->OSTCBBitX;  /* 将该任务置为非就绪态 */
    if (OSRdyTbl[ptcb->OSTCBY] == 0u) {                   /* 若该组只有一个就绪任务，它被非就绪了，那么对应位设置为0 */
        OSRdyGrp           &= (OS_PRIO)~ptcb->OSTCBBitY;
    }

#if (OS_EVENT_EN)
    if (ptcb->OSTCBEventPtr != (OS_EVENT *)0) {  /* 若任务有在等待某事件(Mutex/信号量等) */
        OS_EventTaskRemove(ptcb, ptcb->OSTCBEventPtr); /* 从自己所处的等待列表中删除 */
    }
#if (OS_EVENT_MULTI_EN > 0u)
    if (ptcb->OSTCBEventMultiPtr != (OS_EVENT **)0) {   /* 若任务在等待多个事件 */
        OS_EventTaskRemoveMulti(ptcb, ptcb->OSTCBEventMultiPtr); /* 同样是删除等待事件 */
    }
#endif
#endif

#if (OS_FLAG_EN > 0u) && (OS_MAX_FLAGS > 0u)
    pnode = ptcb->OSTCBFlagNode;      /* 获取等待flag的节点 */
    if (pnode != (OS_FLAG_NODE *)0) { /* 若任务在等待flag */
        OS_FlagUnlink(pnode);         /* 同样删除等待节点 */
    }
#endif

    ptcb->OSTCBDly      = 0u;          /* 清零任务节拍延时 */
    ptcb->OSTCBStat     = OS_STAT_RDY; /* 设置任务为就绪态 */
    ptcb->OSTCBStatPend = OS_STAT_PEND_OK; /* StatPend 置为结束挂起态*/

    if (OSLockNesting < 255u) {   /* 调度锁级别加1，使之不能进行上下文切换。预防触发ISR(即调度，因为调度是又PendSV中断操作的) */
        OSLockNesting++;
    }
    OS_EXIT_CRITICAL();         /* 退出临界区保护 */
    OS_Dummy();                 /* 在这里可能执行ISR，因为临界区已经退出 */
    OS_ENTER_CRITICAL();        /* 进入临界区保护 */
    if (OSLockNesting > 0u) {   /* 调度锁级别减1，因为进入临界区已经不会产生ISR的可能 */
        OSLockNesting--;
    }

    OSTaskDelHook(ptcb);        /* 在任务被删除之前调用钩子函数，钩子函数的内容是用户自己编写的 */
    OSTaskCtr--;                /* 任务计数器自减1 */

    //将被删除的任务的TCB置为NULL，就从优先级表中把TCB删除了
    OSTCBPrioTbl[prio] = (OS_TCB *)0;

    //uCOS-II采用双向链表的形式管理系统中的所有任务的TCB(其实从数据结构上看这些TCB是构成数组的，但是管理采用链表管理)
    //若删除的任务的TCB位于双向链表头
    if (ptcb->OSTCBPrev == (OS_TCB *)0) {               /* Remove from TCB chain                       */
        ptcb->OSTCBNext->OSTCBPrev = (OS_TCB *)0;
        OSTCBList                  = ptcb->OSTCBNext;
    } else {   //不是双向链表头(不可能是链表尾，因为不可能删除空闲任务)
        ptcb->OSTCBPrev->OSTCBNext = ptcb->OSTCBNext;
        ptcb->OSTCBNext->OSTCBPrev = ptcb->OSTCBPrev;
    }
    ptcb->OSTCBNext     = OSTCBFreeList;     /* OSTCBFreeList指向的是处于空闲状态的任务，现将其赋给OSTCBNext */
    OSTCBFreeList       = ptcb;              /* ptcb已被删除，下次需要TCB的空间，即可通过OSTCBFreeList获得 */
#if OS_TASK_NAME_EN > 0u
    ptcb->OSTCBTaskName = (INT8U *)(void *)"?"; /* reset被删除的任务名字 */
#endif  
    OS_EXIT_CRITICAL();
    if (OSRunning == OS_TRUE) {
        OS_Sched();                            /* 若系统正在运行，任务被删除后自然要重新调度 */
    }
    return (OS_ERR_NONE);
}
#endif
```

在代码看到了OS_Dummy()函数，它位于非保护区。其实现体竟然为空：

```#if OS_TASK_DEL_EN > 0
void  OS_Dummy (void)
{
}
#endif
```

在OSTaskDel()函数执行中一直在访问全局变量，即进入临界区的时间太长，系统处于长时间不能响应终端的工作状态，对于实时性的操作系统来说是不可行的。为确保系统实时性，在该函数中退出临界区一段时间去执行OS_Dummy()函数。该函数是个空函数，目的就是给中断一定的时间，然后再关中断，进入临界区继续执行OSTaskDel()。
在OS_Dummy()函数的前面，对系统任务调度器上锁，即OSLockNesting自加1以禁止让任务调度，这是因为uCOS-II是优先级抢占型内核，在OS_Dummy()执行时间内可能出现另一个优先级更高的任务，使得本任务(执行删除操作的任务)被挂起。为避免出现此情况，而又能响应其他中断，OSLockNesting自加1后进入临界区后再自减1。

5. 请求删除任务函数OSTaskDelReq()有时，任务会占用一些动态内存或者信号量之类的资源，这时若由其他任务把这个任务删除了，那么被删除的任务所占用的一些资源可能会因为没有被释放而被丢弃。因此任务删除操作一定要谨慎。具体实现方法是任务A要删除任务B，任务A只负责向任务B提出删除请求，具体删除操作由任务B自己实行，这样任务B就可以根据自身的具体情况来决定自己何时删除自己，同时释放自身所占据的资源。
显然要让任务A和任务B能够按照上述的流程执行删除任务操作，它们之间必须存在某种通信方法，这就利用到了任务的TCB的OSTCBDelReq变量，同时还需要用于请求删除任务的函数OSTaskDelReq()。

```#if OS_TASK_DEL_EN > 0u
INT8U  OSTaskDelReq (INT8U prio)
{
    INT8U      stat;
    OS_TCB    *ptcb;
#if OS_CRITICAL_METHOD == 3u                     /* Allocate storage for CPU status register           */
    OS_CPU_SR  cpu_sr = 0u;
#endif
    /* 空闲任务不可被删除 */
    if (prio == OS_TASK_IDLE_PRIO) {                            /* Not allowed to delete idle task     */
        return (OS_ERR_TASK_DEL_IDLE);
    }
#if OS_ARG_CHK_EN > 0u
    /* prio超出优先级范畴且不为OS_PRIO_SELF */
    if (prio >= OS_LOWEST_PRIO) {                               /* Task priority valid ?               */
        if (prio != OS_PRIO_SELF) {
            return (OS_ERR_PRIO_INVALID);
        }
    }
#endif
    /* 任务A请求删除任务B，B会传参为OS_TASK_IDLE_PRIO调用此函数，以删除自己 */
    if (prio == OS_PRIO_SELF) {                                 /* See if a task is requesting to ...  */
        OS_ENTER_CRITICAL();                                    /* ... this task to delete itself      */
        stat = OSTCBCur->OSTCBDelReq;   /* OSTCBDelReq是一个有任务要删除自身的标志 */
        OS_EXIT_CRITICAL();
        return (stat);      //返回请求状态给调用者
    }
    OS_ENTER_CRITICAL();
    ptcb = OSTCBPrioTbl[prio];          /* 拿到待删除的任务(任务B)的TCB */
    if (ptcb == (OS_TCB *)0) {          /* 要删除的任务并不存在或者已被删除 */               
        OS_EXIT_CRITICAL();
        return (OS_ERR_TASK_NOT_EXIST);                      
    }
    if (ptcb == OS_TCB_RESERVED) {      /* 要删除的任务已经被预定 */ 
        OS_EXIT_CRITICAL();
        return (OS_ERR_TASK_DEL);
    }
    ptcb->OSTCBDelReq = OS_ERR_TASK_DEL_REQ;     /* OS_ERR_TASK_DEL_REQ表示该任务待被删除 */   
    OS_EXIT_CRITICAL();
    return (OS_ERR_NONE);
}
#endif
```
这个函数能被提出删除请求的任务调用，函数参数prio为被删除任务为被删除任务的优先级；被删除任务也可以调用这个函数，函数的参数prio为OS_PRIO_SELF。
提出删除请求的任务调用这个函数的目的是查看被删除的任务控制块是否存在，若存在则令被删除的任务的TCB成员OSTCBDelReq的值为OS_TASK_DEL_REQ，表示通知目的任务要在合适的时机删除它自己。若不在则认为要被删除的任务已经被删除了。例如要删除优先级为12的任务，OSTaskDelReq()的使用代码为：

```while (OSTaskDelReq(12) != OS_ERR_TASK_NOT_EXIST)  //OS_ERR_TASK_NOT_EXIST表示该任务已经被删除或者不存在
{
    OSTimeDly(2);       //延时2个时钟节拍
}
```
被删除的任务调用此函数，参数prio为OS_PRIO_SELF。此函数判断参数为OS_PRIO_SELF后返回TCB的OSTCBDelReq的状态如果有任务要删除自己，那么OSTCBDelReq的状态为OS_TASK_DEL_REQ，那么被删除的任务可以在合适时机调用OSTaskDel()删除自己：

```if (OSTaskDelReq(OS_PRIO_SELF) == OS_TASK_DEL_REQ)
{
    //执行资源和动态内存的代码

    OSTaskDel(OS_PRIO_SELF);
}
else
{
    //执行其他应用代码
}
```

6. 获取任务名字函数OSTaskNameGet()
```#if OS_TASK_NAME_SIZE > 1
INT8U  OSTaskNameGet (INT8U prio, INT8U *pname, INT8U *perr)
{
    OS_TCB    *ptcb;
    INT8U      len;
#if OS_CRITICAL_METHOD == 3                              /* Allocate storage for CPU status register   */
    OS_CPU_SR  cpu_sr = 0;
#endif

#if OS_ARG_CHK_EN > 0
    if (perr == (INT8U *)0) {                            /* Validate 'perr'                            */
        return (0);
    }
    if (prio > OS_LOWEST_PRIO) {                         /* Task priority valid ?                      */
        if (prio != OS_PRIO_SELF) {
            *perr = OS_ERR_PRIO_INVALID;                 /* No                                         */
            return (0);
        }
    }
    if (pname == (INT8U *)0) {                           /* Is 'pname' a NULL pointer?                 */
        *perr = OS_ERR_PNAME_NULL;                       /* Yes                                        */
        return (0);
    }
#endif
    if (OSIntNesting > 0) {                              /* See if trying to call from an ISR          */
        *perr = OS_ERR_NAME_GET_ISR;
        return (0);
    }
    OS_ENTER_CRITICAL();
    if (prio == OS_PRIO_SELF) {                          /* See if caller desires it's own name        */
        prio = OSTCBCur->OSTCBPrio;
    }
    ptcb = OSTCBPrioTbl[prio];
    if (ptcb == (OS_TCB *)0) {                           /* Does task exist?                           */
        OS_EXIT_CRITICAL();                              /* No                                         */
        *perr = OS_ERR_TASK_NOT_EXIST;
        return (0);
    }
    if (ptcb == OS_TCB_RESERVED) {                       /* Task assigned to a Mutex?                  */
        OS_EXIT_CRITICAL();                              /* Yes                                        */
        *perr = OS_ERR_TASK_NOT_EXIST;
        return (0);
    }
    /* 以上代码是进行一系列合法性判断，这一句才是真正拷贝任务名字的地方 */
    len   = OS_StrCopy(pname, ptcb->OSTCBTaskName);      /* Yes, copy name from TCB                    */
    OS_EXIT_CRITICAL();
    *perr = OS_ERR_NONE;
    return (len);
}
#endif
```

7. 设置任务名字函数OSTaskNameSet()
```#if OS_TASK_NAME_SIZE > 1
void  OSTaskNameSet (INT8U prio, INT8U *pname, INT8U *perr)
{
    INT8U      len;
    OS_TCB    *ptcb;
#if OS_CRITICAL_METHOD == 3                          /* Allocate storage for CPU status register       */
    OS_CPU_SR  cpu_sr = 0;
#endif



#if OS_ARG_CHK_EN > 0
    if (perr == (INT8U *)0) {                        /* Validate 'perr'                                */
        return;
    }
    if (prio > OS_LOWEST_PRIO) {                     /* Task priority valid ?                          */
        if (prio != OS_PRIO_SELF) {
            *perr = OS_ERR_PRIO_INVALID;             /* No                                             */
            return;
        }
    }
    if (pname == (INT8U *)0) {                       /* Is 'pname' a NULL pointer?                     */
        *perr = OS_ERR_PNAME_NULL;                   /* Yes                                            */
        return;
    }
#endif
    if (OSIntNesting > 0) {                          /* See if trying to call from an ISR              */
        *perr = OS_ERR_NAME_SET_ISR;
        return;
    }
    OS_ENTER_CRITICAL();
    if (prio == OS_PRIO_SELF) {                      /* See if caller desires to set it's own name     */
        prio = OSTCBCur->OSTCBPrio;
    }
    ptcb = OSTCBPrioTbl[prio];
    if (ptcb == (OS_TCB *)0) {                       /* Does task exist?                               */
        OS_EXIT_CRITICAL();                          /* No                                             */
        *perr = OS_ERR_TASK_NOT_EXIST;
        return;
    }

    if (ptcb == OS_TCB_RESERVED) {                   /* Task assigned to a Mutex?                      */
        OS_EXIT_CRITICAL();                          /* Yes                                            */
        *perr = OS_ERR_TASK_NOT_EXIST;
        return;
    }

    len = OS_StrLen(pname);                          /* Yes, Can we fit the string in the TCB?         */
    if (len > (OS_TASK_NAME_SIZE - 1)) {             /*      No                                        */
        OS_EXIT_CRITICAL();
        *perr = OS_ERR_TASK_NAME_TOO_LONG;
        return;
    }
    //同理，设置任务名字
    (void)OS_StrCopy(ptcb->OSTCBTaskName, pname);    /*      Yes, copy to TCB                          */
    OS_EXIT_CRITICAL();
    *perr = OS_ERR_NONE;
}
#endif
```

8. 挂起任务函数OSTaskSuspend()所谓挂起一个任务，就是停止任务的运行。在uCOS-II中可调用OSTaskSuspend()函数来挂起自身或者除空闲之外的其他任务，用函数OSTaskSuspend()挂起的任务，只能通过恢复函数OSTaskResume()使其恢复为就绪态。

```#if OS_TASK_SUSPEND_EN > 0u
INT8U  OSTaskSuspend (INT8U prio)
{
    BOOLEAN    self;
    OS_TCB    *ptcb;
    INT8U      y;
#if OS_CRITICAL_METHOD == 3u 
    OS_CPU_SR  cpu_sr = 0u;
#endif

#if OS_ARG_CHK_EN > 0u
    if (prio == OS_TASK_IDLE_PRIO) {  //空闲任务不可删除
        return (OS_ERR_TASK_SUSPEND_IDLE);
    }
    if (prio >= OS_LOWEST_PRIO) {   //优先级参数不合法
        if (prio != OS_PRIO_SELF) {
            return (OS_ERR_PRIO_INVALID);
        }
    }
#endif
    OS_ENTER_CRITICAL();
    if (prio == OS_PRIO_SELF) {   //表示挂起自身
        prio = OSTCBCur->OSTCBPrio; 
        self = OS_TRUE;         //等于OS_TRUE表示挂起的是自己
    } else if (prio == OSTCBCur->OSTCBPrio) {   
        self = OS_TRUE;         //等于OS_TRUE表示挂起的是自己
    } else {
        self = OS_FALSE;        //挂起别人
    }
    ptcb = OSTCBPrioTbl[prio];
    if (ptcb == (OS_TCB *)0) {  //任务不存在
        OS_EXIT_CRITICAL();
        return (OS_ERR_TASK_SUSPEND_PRIO);
    }
    if (ptcb == OS_TCB_RESERVED) {   //任务被占领
        OS_EXIT_CRITICAL();
        return (OS_ERR_TASK_NOT_EXIST);
    }

    //操作就绪表。所谓挂起，就是将任务置为非就绪态
    y            = ptcb->OSTCBY;
    OSRdyTbl[y] &= (OS_PRIO)~ptcb->OSTCBBitX;                   /* Make task not ready                 */
    if (OSRdyTbl[y] == 0u) {
        OSRdyGrp &= (OS_PRIO)~ptcb->OSTCBBitY;
    }

    //设置标志，OS_STAT_SUSPEND表挂起态
    ptcb->OSTCBStat |= OS_STAT_SUSPEND;
    OS_EXIT_CRITICAL();
    if (self == OS_TRUE) { //如果当前任务挂起当前任务，那么挂完后重新调度。
                           //如果不重新调度，那么此任务一挂起，系统就挂了
        OS_Sched();        //如果挂起的是别的任务，那么不调度也没关系，因为本任务还是在执行，
                           //当本任务执行完毕或者在适当时机，操作系统就会继续调度
    }
    return (OS_ERR_NONE);
}
#endif
```
该函数的一系列判断主要是判断要被挂起的任务是否是这个函数的任务本身。若是任务本身则置任务在就绪表的就绪标志位非就绪，并在任务控制块成员OSTCBStat中做了挂起记录之后，引发一次系统调度，以使CPU去执行其他就绪的任务；若待挂起的任务是其他任务，那么只要设置就绪标志位非就绪和在任务控制块成员OSTCBStat中做了挂起记录即可。

9. 恢复挂起任务OSTaskResume()
```#if OS_TASK_SUSPEND_EN > 0u
INT8U  OSTaskResume (INT8U prio)
{
    OS_TCB    *ptcb;
#if OS_CRITICAL_METHOD == 3u 
    OS_CPU_SR  cpu_sr = 0u;
#endif

#if OS_ARG_CHK_EN > 0u
    if (prio >= OS_LOWEST_PRIO) { 
        return (OS_ERR_PRIO_INVALID);
    }
#endif
    OS_ENTER_CRITICAL();
    ptcb = OSTCBPrioTbl[prio];
    if (ptcb == (OS_TCB *)0) {
        OS_EXIT_CRITICAL();
        return (OS_ERR_TASK_RESUME_PRIO);
    }
    if (ptcb == OS_TCB_RESERVED) {    
        OS_EXIT_CRITICAL();
        return (OS_ERR_TASK_NOT_EXIST);
    }
    if ((ptcb->OSTCBStat & OS_STAT_SUSPEND) != OS_STAT_RDY) { /* 不等于OS_STAT_RDY即该任务确实处于OS_STAT_SUSPEND状态 */
                                                              /* 等价于if ((ptcb->OSTCBStat & OS_STAT_SUSPEND) == OS_STAT_SUSPEND) */
        ptcb->OSTCBStat &= (INT8U)~(INT8U)OS_STAT_SUSPEND;    /* 清零操作，即去除挂起状态 */
        if (ptcb->OSTCBStat == OS_STAT_RDY) {       /* 清零后不一定就是就绪态，也可能该任务还有其他挂起态，如延时中  */       
            if (ptcb->OSTCBDly == 0u){/* 可能该任务是在延时期间被挂起的，现在去除挂起态，那么让其延时继续，不设置为就绪态度 */

                //既然不存在延时，那么设置该任务为就绪态
                OSRdyGrp               |= ptcb->OSTCBBitY;    /* Yes, Make task ready to run           */
                OSRdyTbl[ptcb->OSTCBY] |= ptcb->OSTCBBitX;
                OS_EXIT_CRITICAL();
                if (OSRunning == OS_TRUE) {  /* 系统处于运行状态，那么开始调度 */
                    OS_Sched();                               /* Find new highest priority task        */
                }
            } else {
                OS_EXIT_CRITICAL();
            }
        } else {                                              /* Must be pending on event              */
            OS_EXIT_CRITICAL();
        }
        return (OS_ERR_NONE);
    }
    OS_EXIT_CRITICAL();
    return (OS_ERR_TASK_NOT_SUSPENDED);
}
#endif
```

OSTaskResume()函数在判断任务确实是一个已存在的挂起任务，同时它又不是一个等待任务(TCB中的成员OSTCBDly=0)时，就清除该任务的TCB中的OSTCBStat中的挂起记录并使任务就绪，最后调度，返回成功信息OS_NO_ERR；若只是个等待任务且状态为挂起态，那么只是单纯清除该任务的TCB中的OSTCBStat中的挂起记录，该任务会继续延时。

10. 查询任务的信息函数OSTaskQuery()任务应用程序在运行中想了解一个任务的指针、堆栈等信息，可以通过函数OSTaskQuery()来获取。
```
#if OS_TASK_QUERY_EN > 0
INT8U  OSTaskQuery (INT8U prio, OS_TCB *p_task_data)
{
    OS_TCB    *ptcb;
#if OS_CRITICAL_METHOD == 3   
    OS_CPU_SR  cpu_sr = 0;
#endif
#if OS_ARG_CHK_EN > 0
    if (prio > OS_LOWEST_PRIO) {   
        if (prio != OS_PRIO_SELF) {
            return (OS_ERR_PRIO_INVALID);
        }
    }
    if (p_task_data == (OS_TCB *)0) {
        return (OS_ERR_PDATA_NULL);
    }
#endif
    OS_ENTER_CRITICAL();
    if (prio == OS_PRIO_SELF) {    
        prio = OSTCBCur->OSTCBPrio;
    }
    ptcb = OSTCBPrioTbl[prio];
    if (ptcb == (OS_TCB *)0) { 
        OS_EXIT_CRITICAL();
        return (OS_ERR_PRIO);
    }
    if (ptcb == OS_TCB_RESERVED) {  
        OS_EXIT_CRITICAL();
        return (OS_ERR_TASK_NOT_EXIST);
    }

    /* 经过上面一系列判断之后，将任务的TCB拷贝给输入型参数 */
    OS_MemCopy((INT8U *)p_task_data, (INT8U *)ptcb, sizeof(OS_TCB));    /* ¿½±´ */
    OS_EXIT_CRITICAL();
    return (OS_ERR_NONE);
}
#endif
```

OSTaskQuery()查询成功函数返回OS_ERR_NONE并将任务TCB信息拷贝到OS_TCB类型的输入参数中。

11. 获取栈的使用状态函数OSTaskStkChk()os_stk_data结构体用于描述栈的使用情况，它作为输入型参数：

```#if OS_TASK_CREATE_EXT_EN > 0u
typedef struct os_stk_data {
    INT32U  OSFree;                    /* 还剩下多少，注意是个数而非字节数 */
    INT32U  OSUsed;                    /* 已经使用了多少，注意是个数而非字节数 */
} OS_STK_DATA;
#endif

#if (OS_TASK_STAT_STK_CHK_EN > 0u) && (OS_TASK_CREATE_EXT_EN > 0u)
INT8U  OSTaskStkChk (INT8U         prio,
                     OS_STK_DATA  *p_stk_data)
{
    OS_TCB    *ptcb;
    OS_STK    *pchk;
    INT32U     nfree;
    INT32U     size;
#if OS_CRITICAL_METHOD == 3u  
    OS_CPU_SR  cpu_sr = 0u;
#endif
#if OS_ARG_CHK_EN > 0u
    if (prio > OS_LOWEST_PRIO) {  
        if (prio != OS_PRIO_SELF) {
            return (OS_ERR_PRIO_INVALID);
        }
    }
    if (p_stk_data == (OS_STK_DATA *)0) {
        return (OS_ERR_PDATA_NULL);
    }
#endif
    p_stk_data->OSFree = 0u; //对输入型参数初始值为0              
    p_stk_data->OSUsed = 0u; 

    OS_ENTER_CRITICAL();
    if (prio == OS_PRIO_SELF) {          
        prio = OSTCBCur->OSTCBPrio;
    }
    ptcb = OSTCBPrioTbl[prio];  //拿到对应该任务的TCB
    if (ptcb == (OS_TCB *)0) {             
        OS_EXIT_CRITICAL();
        return (OS_ERR_TASK_NOT_EXIST);
    }
    if (ptcb == OS_TCB_RESERVED) {
        OS_EXIT_CRITICAL();
        return (OS_ERR_TASK_NOT_EXIST);
    }

    //监测是否支持栈监测功能
    if ((ptcb->OSTCBOpt & OS_TASK_OPT_STK_CHK) == 0u) {
        OS_EXIT_CRITICAL();
        return (OS_ERR_TASK_OPT);
    }
    nfree = 0u;
    size  = ptcb->OSTCBStkSize;     /* 栈的大小(栈内空间的个数，stm32中每个空间大小为32BIT) */
    pchk  = ptcb->OSTCBStkBottom;   /* 栈底 */ 
    OS_EXIT_CRITICAL();

#if OS_STK_GROWTH == 1u             /* 1表示减栈 */
    while (*pchk++ == (OS_STK)0) {  /* 内容为0的栈地方表示还未被使用 */
        nfree++;
    }
#else
    while (*pchk-- == (OS_STK)0) {  
        nfree++;
    }
#endif
    p_stk_data->OSFree = nfree;         //注意是个数而非字节数
    p_stk_data->OSUsed = size - nfree;  //注意是个数而非字节数          
    return (OS_ERR_NONE);
}
#endif
```

12. 清零任务栈空间函数OS_TaskStkClr()清零任务栈，一般是在任务被删除后调用的。

```#if (OS_TASK_STAT_STK_CHK_EN > 0u) && (OS_TASK_CREATE_EXT_EN > 0u)
void  OS_TaskStkClr (OS_STK  *pbos,     //栈底
                     INT32U   size,     //栈大小
                     INT16U   opt)      //工作选项
{
    //判断是否支持OS_TASK_OPT_STK_CHK功能
    if ((opt & OS_TASK_OPT_STK_CHK) != 0x0000u) {      /* See if stack checking has been enabled       */
        //判断是否支持清理栈功能
        if ((opt & OS_TASK_OPT_STK_CLR) != 0x0000u) {  
#if OS_STK_GROWTH == 1u                 //降栈
            while (size > 0u) { 
                size--;
                *pbos++ = (OS_STK)0;    /* 从栈底开始往上一个一个空间置零，置零size个空间 */
            }
#else
            while (size > 0u) {                        /* Stack grows from LOW to HIGH memory          */
                size--;
                *pbos-- = (OS_STK)0;                   /* Clear from bottom of stack and down          */
            }
#endif
        }
    }
}

#endif
```
清零的空间大小为size，所以size数值十分重要，给大了可能会置零一些重要数据，如栈在初始化时有16个寄存器用于保存栈帧结构，如果这些数据被置零了就没得玩了。

13. 任务返回函数OS_TaskReturn()这是V2.89版本以后才有的函数。uCOS-II中是不允许任务返回的，若任务错误的返回了，OS_TaskReturn()或捕捉错误并删除出错任务。OS_TaskReturn()通过调用OSTaskReturnHook()进而调用App_TaskreturnHook()来实现任务出错后的执行的用于定义的操作。

```void  OS_TaskReturn (void)
{
    OSTaskReturnHook(OSTCBCur);     /* 任务返回的钩子函数 */

#if OS_TASK_DEL_EN > 0u
    (void)OSTaskDel(OS_PRIO_SELF);                /* Delete task if it accidentally returns!           */
#else
    for (;;) {
        OSTimeDly(OS_TICKS_PER_SEC);
    }
#endif
}
```

14. 获取任务寄存器的当前值OSTaskRegGet()
```#if OS_TASK_REG_TBL_SIZE > 0u
INT32U  OSTaskRegGet (INT8U   prio, //任务的优先级
                      INT8U   id,   //任务寄存器的ID
                      INT8U  *perr) //输出型参数，用于存放出错信息
{
#if OS_CRITICAL_METHOD == 3u                     /* Allocate storage for CPU status register           */
    OS_CPU_SR  cpu_sr = 0u;
#endif
    INT32U     value;
    OS_TCB    *ptcb;



#ifdef OS_SAFETY_CRITICAL
    if (perr == (INT8U *)0) {
        OS_SAFETY_CRITICAL_EXCEPTION();
        return (0u);
    }
#endif

#if OS_ARG_CHK_EN > 0u
    if (prio >= OS_LOWEST_PRIO) {
        if (prio != OS_PRIO_SELF) {
            *perr = OS_ERR_PRIO_INVALID;
            return (0u);
        }
    }
    if (id >= OS_TASK_REG_TBL_SIZE) {
        *perr = OS_ERR_ID_INVALID;
        return (0u);
    }
#endif
    OS_ENTER_CRITICAL();
    if (prio == OS_PRIO_SELF) {                  /* See if need to get register from current task      */
        ptcb = OSTCBCur;
    } else {
        ptcb = OSTCBPrioTbl[prio];
    }
    value = ptcb->OSTCBRegTbl[id];
    OS_EXIT_CRITICAL();
    *perr = OS_ERR_NONE;
    return (value);
}
#endif
```

这个函数被调用来获取任务寄存器的当前值。任务寄存器是特定于应用程序的，可用于存储特定于任务的值。

15. 分配下一个可用任务寄存器id函数OSTaskRegGetID()
```#if OS_TASK_REG_TBL_SIZE > 0u
INT8U  OSTaskRegGetID (INT8U  *perr)
{
#if OS_CRITICAL_METHOD == 3u                                    /* Allocate storage for CPU status register           */
    OS_CPU_SR  cpu_sr = 0u;
#endif
    INT8U      id;


#ifdef OS_SAFETY_CRITICAL
    if (perr == (INT8U *)0) {
        OS_SAFETY_CRITICAL_EXCEPTION();
        return ((INT8U)OS_TASK_REG_TBL_SIZE);
    }
#endif

    OS_ENTER_CRITICAL();
    if (OSTaskRegNextAvailID >= OS_TASK_REG_TBL_SIZE) {         /* See if we exceeded the number of IDs available     */
       *perr = OS_ERR_NO_MORE_ID_AVAIL;                         /* Yes, cannot allocate more task register IDs        */
        OS_EXIT_CRITICAL();
        return ((INT8U)OS_TASK_REG_TBL_SIZE);
    }

    id   = OSTaskRegNextAvailID;                                /* Assign the next available ID                       */
    OSTaskRegNextAvailID++;                                     /* Increment available ID for next request            */
    OS_EXIT_CRITICAL();
   *perr = OS_ERR_NONE;
    return (id);
}
#endif

```
这个函数被调用来获得一个任务寄存器ID。这个函数允许任务寄存器ID为动态地而不是静态地分配。

16. 改变任务寄存器的当前值函数OSTaskRegSet()
```#if OS_TASK_REG_TBL_SIZE > 0u
void  OSTaskRegSet (INT8U    prio,
                    INT8U    id,
                    INT32U   value,
                    INT8U   *perr)
{
#if OS_CRITICAL_METHOD == 3u                     /* Allocate storage for CPU status register           */
    OS_CPU_SR  cpu_sr = 0u;
#endif
    OS_TCB    *ptcb;


#ifdef OS_SAFETY_CRITICAL
    if (perr == (INT8U *)0) {
        OS_SAFETY_CRITICAL_EXCEPTION();
        return;
    }
#endif

#if OS_ARG_CHK_EN > 0u
    if (prio >= OS_LOWEST_PRIO) {
        if (prio != OS_PRIO_SELF) {
            *perr = OS_ERR_PRIO_INVALID;
            return;
        }
    }
    if (id >= OS_TASK_REG_TBL_SIZE) {
        *perr = OS_ERR_ID_INVALID;
        return;
    }
#endif
    OS_ENTER_CRITICAL();
    if (prio == OS_PRIO_SELF) {                  /* See if need to get register from current task      */
        ptcb = OSTCBCur;
    } else {
        ptcb = OSTCBPrioTbl[prio];
    }
    ptcb->OSTCBRegTbl[id] = value;
    OS_EXIT_CRITICAL();
    *perr                 = OS_ERR_NONE;
}
#endif
```
OSTaskRegSet()、OSTaskRegGetID()、OSTaskRegGet()也是较新版本的uCOS-II才增加的函数。具体用法，用到的时候再细究。

---