# uCOS-II系统中的任务

uCOS-II系统内核的主要工作是对任务的管理和调度.

1. 任务的引入
在公司的大型的软件研发项目中，通常项目经理会将该项目分解成多个功能模块，项目组内程序员分别负责其中一个，当这多个功能模块完成时候，就意味着整个项目进度接近完成。当然，在开发过程中，项目组内的程序员是同时在工作的，即所谓的“并行开发”，这将大大提高了项目完成效率。

在uCOS-II中，上述的“功能模块”就是“任务”，uCOS-II就是一个能对这些任务的运行进行调度、管理，从而实现并发方式执行这些任务的多任务操作系统。

2. 任务控制块
uCOS-II系统中的任务从代码上看，依旧是一个个c函数，但是作为该函数要成为能被操作系统调度管理的任务，就应该具有一个控制数据结构，这就是任务控制块。

任务的任务控制块(TCB)相当于一个任务的身份证，系统就是通过任务控制块来管理任务的，没有任务控制块的任务就不是一个任务，因为它不能被系统管理。当用户应用程序调用OSTackCreate()函数创建一个任务时，该函数就会对任务控制块中所有成员(记录任务的堆栈指针、任务的当前状态，任务优先级别)赋予该任务相关的数据，并记录在RAM中。

```//位于ucos-ii/source/ucos_ii.h
typedef struct os_tcb {
    OS_STK          *OSTCBStkPtr;   //指向任务的私有栈的栈顶

#if OS_TASK_CREATE_EXT_EN > 0       // 早期的ucos创建任务其属性非常简单，后期想赋予任务更多的属性时，
                                    // 为了兼容老的代码，多了这个配置宏，让操作系统使用者自己决定使用新属性否,EXT理解为扩展的

    void            *OSTCBExtPtr;           // 指向用户可定义的数据，这些数据是为TCB某些功能服务的
    OS_STK          *OSTCBStkBottom;        // 指向任务的私有栈的栈底
    INT32U           OSTCBStkSize;          // 栈元素的个数，假设栈中有100个元素，每个元素占据4字节，共400字节。OSTCBStkSize则为100 */
    INT16U           OSTCBOpt;              // 可选项
    INT16U           OSTCBId;               // 任务的ID，区分任务用
#endif

    struct os_tcb   *OSTCBNext;             // 双向链表，指向下一个任务
    struct os_tcb   *OSTCBPrev;             // 双向链表，指向上一个任务

#if (OS_EVENT_EN) || (OS_FLAG_EN > 0)
    OS_EVENT        *OSTCBEventPtr;         // Even指的是两个任务间的通信，如信号量、消息盒子、Mutex等
#endif

#if (OS_EVENT_EN) && (OS_EVENT_MULTI_EN > 0)
    OS_EVENT       **OSTCBEventMultiPtr;    /* Pointer to multiple event control blocks */
#endif

#if ((OS_Q_EN > 0) && (OS_MAX_QS > 0)) || (OS_MBOX_EN > 0)
    void            *OSTCBMsg;              // 指向传递给任务消息的指针
#endif

#if (OS_FLAG_EN > 0) && (OS_MAX_FLAGS > 0)
#if OS_TASK_DEL_EN > 0                      /* 任务删除 */
    OS_FLAG_NODE    *OSTCBFlagNode;         /* Pointer to event flag node                              */
#endif
    OS_FLAGS         OSTCBFlagsRdy;         /* 让任务变为rdy的那个flag */    /* Event flags that made task ready to run                 */
#endif

    INT16U           OSTCBDly;              /* 等待一个event所要的tick的数目，Nbr ticks to delay task or, timeout waiting for event   */
    INT8U            OSTCBStat;             // 任务的当前状态标志
    INT8U            OSTCBStatPend;         // 挂起状态
    INT8U            OSTCBPrio;             // 任务优先级，每个优先级只能一个任务

    //用于快速访问任务就绪表的数据
    INT8U            OSTCBX;                /* Bit position in group  corresponding to task priority   */
                                            /* ucos中有一张就绪表，记录就绪的任务和非就绪的任务，最高优先级的就绪状态的任务会得到执行， 这个任务会被记录在组中的一个位*/
    INT8U            OSTCBY;                /* Index into ready table corresponding to task priority   */
                                            /* OSTCBY也是跟就绪表有关 */
#if OS_LOWEST_PRIO <= 63                    /* 操作系统最低的优先级，说白了指操作系统中支持多少个优先级，最大为 254，0-254为255个级别*/
    INT8U            OSTCBBitX;             /* Bit mask to access bit position in ready table          */
    INT8U            OSTCBBitY;             /* Bit mask to access bit position in ready group          */
#else
    INT16U           OSTCBBitX;             /* Bit mask to access bit position in ready table          */
    INT16U           OSTCBBitY;             /* Bit mask to access bit position in ready group          */
#endif

#if OS_TASK_DEL_EN > 0
    INT8U            OSTCBDelReq;           // 标识位，设置后就是告诉所在任务，使其自己删除自己
                                            //只有自己删除自己才会删除干净，因为只有它清除该如何删除最好
#endif

#if OS_TASK_PROFILE_EN > 0                  /* 当前任务的参数 */
    INT32U           OSTCBCtxSwCtr;         // 计数当前任务被切换的次数 
    INT32U           OSTCBCyclesTot;        /* 当前任务运行了多少个时钟周期 */
    INT32U           OSTCBCyclesStart;      /* 记录任务恢复时的时钟周期是多少 */
    OS_STK          *OSTCBStkBase;          /* 指向任务栈的起始位置 */
    INT32U           OSTCBStkUsed;          /* 当前任务使用了多少栈 */
#endif

#if OS_TASK_NAME_SIZE > 1                   /* 任务名字的字符数 */
    INT8U            OSTCBTaskName[OS_TASK_NAME_SIZE];
#endif
} OS_TCB;
```

uCOS-II在初始化的时候会按照配置文件所设定的任务数事先定义一些空白任务控制块，当用户程序创建一个任务时，其控制块只要从中拿出一个空白的控制块填上任务的属性即可。以配置定义了32个任务数为例，系统在管理这32个任务控制块使用了两个链表，一个是空白任务块链表(其间的控制块还没分配给任务)，另一个是任务控制块链表(其间的控制块已都分配给任务)。具体做法是，函数OSInit()对系统初始化时，先在RAM中创建一个OS_TCB结构体类型的数据OSTCBTbl[]，并将各个元素链接成一个链表，从而形成空白TCB链表：
![5_TCB链表.png](https://s2.loli.net/2022/01/07/OXLBdGcetq3DFaR.png)


空任务链表的元素总数为OS_MAX_TASKS(定义在os_cfg.h中)，而OS_N_SYS_TASKS(定义在ucos_ii.h中)定义了系统任务的个数。当应用程序调用OSTaskCreate()或者OSTaskCreateExt()创建一个任务时，系统就会将空任务块链表头指针OSTCBFreeList指向的任务控制块分配给该任务，对其个成员赋值后，就将其加入到任务控制块中。(关于系统任务见第4.2点)
![5_TCB链表2.png](https://s2.loli.net/2022/01/07/ScdQpgMVJKEwHWx.png)



如上图表示用户创建了两个用户任务并使用了两个系统任务的情况下(白色为空任务块链表，灰色为任务块链表)。这个加入操作即为任务块的初始化，执行函数为OSTCBInit()：

```OS_TCBInit(INT8U prio,      // 任务的优先级
            OS_STK *ptos,   // 任务堆栈的栈顶指针
            OS_STK *pbos,   // 任务堆栈的栈底指针
            INT16U id,      // 任务的id，在uCOS-II中本量无用
            INT32U stk_size, //任务堆栈的长度
            void *pext,     // 任务控制块的扩展指针
            INT16U opt)     // 任务控制块的选项
```

主要实现为新创建的任务从空任务控制块中获取一个任务控制块，为其赋值，并将其加入任务控制块链表中。

考虑到系统运行效率，uCOS-II还定义一个数据类型为OS_TCB*[] 的数据OSPrioTbl []，该数组以任务的优先级为顺序将各个任务控制块的指针为元素，这样在访问一个任务的任务控制块时就可以不必遍历任务控制块链表了。除此，系统还定义了正在占有CPU的任务所属的控制块称为当前任务控制块，即变量OSTCBCur指针，该指针指向当前任务控制块。

OSTaskDel()用于删除一个任务，实际上就是将该任务的任务控制块从任务控制块链表中删掉，并将控制块归还给空任务控制块。

3. 任务堆栈
堆栈是指存储器中按照数据的先入后出的原则组织的连续存储空间，用于保存任务切换和响应中断、函数调用时CPU寄存器中的内容。

在之前的单片机裸板程序中，只有一个main()函数，所以整个程序只有一个堆栈，其它函数都和main()函数共用此堆栈。到了uCOS-II，每个任务在操作系统看来，已经都是一个独立的运行单元，类似是处于不同平台上的main()函数，自然，它们各自需要一个属于任务本身的私有堆栈。

uCOS-II中定义了一种数据类型OS_TSK：

`typedef unsigned int   OS_STK;  /* Each stack entry is 32-bit wide */`

用户在定义任务堆栈的栈区时：

```#define APP_TASK_START_STK_SIZE 128
static  OS_STK App_TaskStartStk[APP_TASK_START_STK_SIZE];
```
堆栈的增长方向是随系统所使用处理的不同而不同的，有的处理器的堆栈增长方向是向上的，也有的处理器是向下增长的。ARM是满降栈的，STM32亦是如此。

为了提高应用程序的可移植性，创建用户任务的OSTaskcRCreate()的实现为：

```#define APP_TASK_START_STK_SIZE 128
static  OS_STK App_TaskStartStk[APP_TASK_START_STK_SIZE];

void main(void)
{
    //...
#if OS_STK_GROWTH == 1  /* 减栈 */
    OSTaskcRCreate(my_test_task,        //任务函数
                    NULL,               //传给任务函数的参数
                    &App_TaskStartStk[APP_TASK_START_STK_SIZE - 1], //任务栈栈顶的地址
                    16);                //任务的优先级别
#else                   /* 增栈 */
    OSTaskcRCreate(my_test_task, 
                    NULL, 
                    &App_TaskStartStk[0], //任务栈栈底的地址
                    16);
    //...
}
```

每个任务的堆栈保存的都是任务的私有数据，例如指向任务函数的指针，程序状态字PSW等，为此，每启动一个任务都需要对各自的堆栈进行初始化，将CPU各寄存器的初始值数据放在任务堆栈中，当任务获得CPU的使用权时，就把堆栈的内容复制到CPU的各个寄存器，从而可使任务顺利启动并执行。堆栈初始化的函数为：

`OS_STK *OSTaskStkInit (void (*task)(void *p_arg), void *p_arg, OS_STK *ptos, INT16U opt)`

这个函数一般是由OSTaskcRCreate()的实现体调用的，用户一般不会接触这个函数。实现体在os_cpu_c.c中。因为每个处理器对堆栈的初始化不同，在进行移植到不同平台时候一般需要用户自行编写。

每个任务的任务控制块要被uCOS-II的内核函数调用，它被保存在全局数据区中，那任务控制块如何跟任务真正执行的任务函数挂钩？

到这里牵扯出了3个概念：任务控制块、任务堆栈和任务函数，它们之间的关系是什么？可以这么推导：

(1) 任务函数的执行肯定需要堆栈，因为函数的执行不可避免的会遇到函数调用和中断服务，过程中涉及的函数断点需要被保存在堆栈当中，因此可以推导出，任务堆栈中有一个指针，指向任务函数的断点。那在任务堆栈中是不是还需要一个指针指向任务函数的起始地址？答案是不需要，因为任务函数的起始地址也是一个断点。

(2) 任务控制块跟任务函数挂钩，那只需要在块内定义一个指针指向任务的堆栈即可。

所以这3者的关系可以概括下图：
![5_任务控制关系.png](https://s2.loli.net/2022/01/07/TFD2aXi5fSRLcpu.png)

系统要实现对多个任务进行管理，那么需要将这些任务各自的控制块链接起来：

![5_控制块链接.png](https://s2.loli.net/2022/01/07/7nL6qOrgU3pSRMF.png)
如图所示称为任务注册表，将任务控制块加入链表的操作称为任务的注册。

4. 用户任务和系统任务
4.1 用户任务
在嵌入式系统中，任务的执行代码同时是一个无限循环结构(一次性运行任务除外)，在循环结构中可以响应终端，伪代码为：
```
void my_test_task(void* pdata)  //void类型指针，可以接收各种类型的数据(包括函数指针)
{
    while(true)
    {
        //可以被中断的用户代码

        OS_ENTER_CRITICAL();    //进入临界区
        //这里是不可被中断的用户代码
        OS_EXTI_CRITICAL();     //出临界区

        //可以被中断的用户代码
    }
}
```

有了如上的任务函数外，还需要任务堆栈空间：

`static OS_STK App_TaskStartStk[128];`

这时候就可以通过uCOS-II提供的任务创建函数OSTaskcRCreate()即可为任务函数创建任务控制块，从而使得任务函数在内存中可接受系统管理和调度。下面是多个任务的程序结构：
```
//定义用户任务1
void my_test_task1(void* pdata)
{
    while (true)
    {
        //...
    }
}

//定义用户任务2
void my_test_task2(void* pdata)
{
    while (true)
    {
        //...
    }
}

//用户任务3
void my_test_task3(void* pdata)
{
    while (true)
    {
        //...
    }
}

void main(void)
{
    //...
    OSInit();
    //...

    //在系统中创建用户任务
    OSTaskcRCreate(my_test_task1, ...); 
    OSTaskcRCreate(my_test_task2, ...);
    OSTaskcRCreate(my_test_task3, ...);
    //...

    //启动系统，系统启动后任务交由系统管理调度
    OSStart();

    //...
}
```

4.2 系统任务
操作系统除了要管理用户任务之外，还需要处理一些内部事务。对于嵌入式硬件来说，除了是掉电或者时钟脉冲丢失，否则是不能停止工作的，但是在系统运行后，不能排除没有一个用户任务的情况，所以需要一个任务，哪怕只是空操作的循环。这个任务就属于系统任务。

uCOS-II定义了两个系统任务：空闲任务和统计任务。

空闲任务：
系统在运行中可能在某个时间内无用户任务可运行而处于空闲状态，为了使CPU在没有用户任务可执行时有事可做，uCOS-II提供了一个空闲任务OSTaskIdle()：

/* 空任务的具体执行函数，位于os_core.c */
```void  OS_TaskIdle (void *p_arg)
{
#if OS_CRITICAL_METHOD == 3     /* Allocate storage for CPU status register */
    OS_CPU_SR  cpu_sr = 0;
#endif
   (void)p_arg;                 /* Prevent compiler warning for not using 'p_arg' */
    for (;;) {
        OS_ENTER_CRITICAL();
        OSIdleCtr++;            /* 只是执行自加全局变量OSIdleCtr */
        OS_EXIT_CRITICAL();
        OSTaskIdleHook();       /* Call user definable HOOK */
    }
}
```

uCOS-II规定，系统中必须使用空闲任务，且该任务不能通过程序删除。

统计任务：
统计任务用于每1S计算一次CPU在单位内被使用的时间，并把计算结果以百分比的形式存放在变量OSCPUsage中，便于其他应用程序来获取CPU的利用率。

```#if OS_TASK_STAT_EN > 0
void  OS_TaskStat (void *p_arg)
{
#if OS_CRITICAL_METHOD == 3    
    OS_CPU_SR  cpu_sr = 0;
#endif

   (void)p_arg;
    /* 计算OSIdleCtrMax */
    while (OSStatRdy == OS_FALSE) {             /* 统计任务没有被调度，为OS_FALSE */
        OSTimeDly(2 * OS_TICKS_PER_SEC / 10);   /* 延时，一次200ms */
                                                /* 延时期间空任务在跑，即OSIdleCtrRun一直在叠加 */
    }
    OSIdleCtrMax /= 100L;   /* 除以100即去掉小数点 */
    if (OSIdleCtrMax == 0L) {
        OSCPUUsage = 0;     /* 计算OSCPUUsage是本函数的关键实现，即CPU的使用率 */
        (void)OSTaskSuspend(OS_PRIO_SELF);      /* 挂起当前(统计)任务 */
    }

    for (;;) {
        OS_ENTER_CRITICAL();
        OSIdleCtrRun = OSIdleCtr; 
        OSIdleCtr    = 0L;                      /* 清空全局变量。因为cpu的使用率是变化的，所以要清零后让其被自加，以便下次统计 */ /* Reset the idle counter for the next second         */
        OS_EXIT_CRITICAL();

     /* 在某个时间内(200ms)单独跑空闲任务计算得到OSIdleCtrMax */
     /* OSIdleCtrRun则是在系统调度中，空闲任务被执行的次数 */
        OSCPUUsage   = (INT8U)(100L - OSIdleCtrRun / OSIdleCtrMax);     
        OSTaskStatHook();
#if (OS_TASK_STAT_STK_CHK_EN > 0) && (OS_TASK_CREATE_EXT_EN > 0)
        OS_TaskStatStkChk();
#endif
        OSTimeDly(OS_TICKS_PER_SEC / 10);  /* 休眠100ms */
    }
}
#endif
```

是否使用统计任务，用户可以根据OS_TASK_STAT_EN宏来配置使能与否。

5. 任务的状态
在uCOS-II中，每一个具体时刻只会有一个任务占据CPU而处于运行状态(多核CPU不考虑)，那么其他任务只能处于其它状态。uCOS-II系统的任务共有5种状态：

(1) 睡眠态：任务在么有被分配任务控制块或者任务控制台被剥夺的状态

(2) 就绪态：任务具备了运行的所有条件：已分配到任务控制块，已在任务就绪表中记录

(3) 运行态：处于就绪态的任务经系统调度获得CPU的使用权，任务就进入就绪态。就绪的任务只有当所有高于本任务优先级的任务都处于等待态才能进入运行态

(4) 等待态：正在运行的任务需要等待一段时间或者需要等待一个事件的发生(event)的发生再运行时，该任务就会将CPU的使用权让给其他任务而让自己进入等待态

(5) 中断服务状态：一个正在运行的任务一旦响应终端请求就会中止当前的运行转而去执行中断服务程序(下称ISR)，此时任务的状态就叫做中断服务状态

6. 任务的优先级
当有多个任务处于就绪状态时，系统需要在这些任务中选择一个来运行。就绪任务有多个，CPU却有一个，所以CPU需要一个规则来进行选择。uCOS-II采用优先级抢占规则。系统中的每一个任务根据其重要性都配有一个唯一的优先级(uCOS-II中，每一个优先级只能有一个任务)，优先级高的任务先得到执行，优先级低的任务后执行。(数值越小优先级越高)

uCOS-II中最多可创建64个任务，那么任务的优先级别最多有64个。实际上并不需要64个任务这么多，假设我们只是需要32个，那么在系统配置文件的将OS_LOWEST_PRIO设置为31。(OS_LOWEST_PRIO表示最低优先级)

系统会自动将空闲任务的优先级设置为OS_LOWEST_PRIO，在使能统计任务的前提下，OS_LOWEST_PRIO - 1将赋值给统计任务。因此用户任务最多为30个，其优先级为0、1、2…30，用户任务的优先级由用户在创建一个任务时显式指定。(OSTaskCreate()的第4个参数)

uCOS-II中的任务基本的概念大致如此，接下来再记录任务就绪表以及任务调度相关，这些也都是RTOS核心技术。

---
