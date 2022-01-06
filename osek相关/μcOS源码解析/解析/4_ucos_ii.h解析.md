# ucos_ii.h 解析

定位到uCOS-II/Source目录下,此目录是系统的核心代码.

1. 宏定义类型以及头文件包含
```
#define OS_VERSION  29207u  //定义版本号

#include <app_cfg.h>
#include <os_cfg.h>
#include <os_cpu.h>

#ifdef   OS_GLOBALS
#define  OS_EXT
#else
#define  OS_EXT  extern
#endif

#ifndef  OS_FALSE
#define  OS_FALSE       0u
#endif

#ifndef  OS_TRUE
#define  OS_TRUE        1u
#endif

#define  OS_ASCII_NUL   (INT8U)0
#define  OS_PRIO_SELF   0xFFu   /* Indicate SELF priority */
```

OS_PRIO_SELF被宏定义为0xFF，从注释上看OS_PRIO_SELF代表的是任务自身的优先级。为什么是0xff？这宏是适用于当你不知道任务的优先级但是又要操作任务的优先级的时候，uCOS-II的内部函数会将其转换为真正优先级的代码。例如你想用OSTaskDel()删除当前任务但是你又不知道当前任务的优先级，可以写为：

`OSTaskDel(OS_PRIO_SELF);`

```
#if OS_TASK_STAT_EN > 0
#define  OS_N_SYS_TASKS 2u      /* Number of system tasks */
#else
#define  OS_N_SYS_TASKS 1u
#endif
```

OS_TASK_STAT_EN是一个配置宏，OS_TASK_STAT_EN > 0表示使用系统中的统计任务。统计任务是属于系统任务，默认开启且无法被删除的系统任务还有一个空闲任务。当使能了系统统计任务，那么OS_N_SYS_TASKS=2，反之OS_N_SYS_TASKS=1。
```
#define  OS_TASK_STAT_PRIO  (OS_LOWEST_PRIO - 1)
#define  OS_TASK_IDLE_PRIO  (OS_LOWEST_PRIO) 
```
OS_TASK_STAT_PRIO、OS_TASK_IDLE_PRIO分别是统计任务、空闲任务的优先级，OS_LOWEST_PRIO为系统任务的最低优先级。假设系统为最多支持32个任务，那么任务的最低优先级为31(优先级数值越大，优先级越低)。倒数两个低优先级分别赋给**统计任务和空闲任务**。OS_TASK_STAT_PRIO = 30，OS_TASK_IDLE_PRIO = 29。统计任务用于统计系统各种状态参数，如内存/CPU使用率等，空闲任务在系统中无任务可执行时才轮到它执行。
```
#if OS_LOWEST_PRIO <= 63
#define  OS_EVENT_TBL_SIZE ((OS_LOWEST_PRIO) / 8 + 1)   /* Size of event table */
#define  OS_RDY_TBL_SIZE   ((OS_LOWEST_PRIO) / 8 + 1)   /* Size of ready table */
#else
#define  OS_EVENT_TBL_SIZE ((OS_LOWEST_PRIO) / 16 + 1)  /* Size of event table */
#define  OS_RDY_TBL_SIZE   ((OS_LOWEST_PRIO) / 16 + 1)  /* Size of ready table */
#endif
```

OS_RDY_TBL_SIZE是任务就绪表的下标取值范围，OS_LOWEST_PRIO=31， 这里计算得出OS_RDY_TBL_SIZE等于4，即下标取值为0~3。OS_EVENT_TBL_SIZE同理。
```
#define  OS_TASK_IDLE_ID    65535u  /* ID numbers for Idle, Stat and Timer tasks */
#define  OS_TASK_STAT_ID    65534u
#define  OS_TASK_TMR_ID     65533u
```

Idle、Stat、Timer任务的ID，为什么是65535？因为uCOS-II最多支持2^16个任务，其ID最大为65535。在uCOS-II中id值并没什么用处。
```
#define  OS_EVENT_EN  (((OS_Q_EN > 0) && (OS_MAX_QS > 0)) || (OS_MBOX_EN > 0) || (OS_SEM_EN > 0) || (OS_MUTEX_EN > 0))
#define  OS_TCB_RESERVED ((OS_TCB *)1)
```
OS_EVENT_EN为1表示开启系统的事件功能机制。
```
#define  OS_STAT_RDY        0x00u    /* Ready to run (就绪态) */
#define  OS_STAT_SEM        0x01u    /* Pending on semaphore (因等待信号量而被挂起) */
#define  OS_STAT_MBOX       0x02u    /* Pending on mailbox (因等效MBox而被挂起) */
#define  OS_STAT_Q          0x04u    /* Pending on queue (因等待消息队列而被挂起) */
#define  OS_STAT_SUSPEND    0x08u    /* Task is suspended (挂起态) */
#define  OS_STAT_MUTEX      0x10u    /* Pending on mutual exclusion semaphore (因等待Mutex而被挂起) */
#define  OS_STAT_FLAG       0x20u    /* Pending on event flag group (因等待flag而被挂起) */
#define  OS_STAT_MULTI      0x80u    /* Pending on multiple events (因等待MULTI而被挂起，MULTI指代所有事件类型的综合) */
#define  OS_STAT_PEND_ANY   (OS_STAT_SEM | OS_STAT_MBOX | OS_STAT_Q | OS_STAT_MUTEX | OS_STAT_FLAG)
```

如上宏表示任务当前的运行状态，是TCB中OSTCBStat成员的取值选项。
```
#define  OS_STAT_PEND_OK              0u  /* 已经挂起结束或没有挂起 */
#define  OS_STAT_PEND_TO              1u  /* 在有超时机制的挂起状态中 */
#define  OS_STAT_PEND_ABORT           2u  /* 挂起出错 */
```

如上宏表示任务当前的挂起状态，也是TCB中OSTCBStatPend成员的取值选项。
```
#define  OS_EVENT_TYPE_UNUSED         0u
#define  OS_EVENT_TYPE_MBOX           1u
#define  OS_EVENT_TYPE_Q              2u
#define  OS_EVENT_TYPE_SEM            3u
#define  OS_EVENT_TYPE_MUTEX          4u
#define  OS_EVENT_TYPE_FLAG           5u

#define  OS_TMR_TYPE                  100u

```

如上宏表示系统中的事件类型。

```
#define  OS_FLAG_WAIT_CLR_ALL         0u    /* Wait for ALL    the bits specified to be CLR (i.e. 0)   */
#define  OS_FLAG_WAIT_CLR_AND         0u

#define  OS_FLAG_WAIT_CLR_ANY         1u    /* Wait for ANY of the bits specified to be CLR (i.e. 0)   */
#define  OS_FLAG_WAIT_CLR_OR          1u

#define  OS_FLAG_WAIT_SET_ALL         2u    /* Wait for ALL    the bits specified to be SET (i.e. 1)   */
#define  OS_FLAG_WAIT_SET_AND         2u

#define  OS_FLAG_WAIT_SET_ANY         3u    /* Wait for ANY of the bits specified to be SET (i.e. 1)   */
#define  OS_FLAG_WAIT_SET_OR          3u

#define  OS_FLAG_CONSUME           0x80u    /* Consume the flags if condition(s) satisfied             */
#define  OS_FLAG_CLR                  0u
#define  OS_FLAG_SET                  1u
```

跟flag事件相关的宏定义。
```
#if OS_TICK_STEP_EN > 0
#define  OS_TICK_STEP_DIS             0u    /* Stepping is disabled, tick runs as mormal               */
#define  OS_TICK_STEP_WAIT            1u    /* Waiting for uC/OS-View to set OSTickStepState to _ONCE  */
#define  OS_TICK_STEP_ONCE            2u    /* Process tick once and wait for next cmd from uC/OS-View */
#endif
```
uC/OS-View使用。uC/OS-View是一个基于uCOS-II的中间件监控程序，通过串口同windows平台上的客户端程序Viewer配合使用，可以实时显示uCOS-II及其所有任务的当前状态，如任务栈起始地址，栈大小，任务名称，任务当前状态，任务被执行次数和CPU占用率等。最重要的一点是，uC/OS-View已经被Micrium无情抛弃了，所以先不细究。
``
#define  OS_DEL_NO_PEND 0u
#define  OS_DEL_ALWAYS  1u
``

删除事件函数，如OSSemDel()、OSMboxDel()等，其opt参数的取值选项。前者表示若有任务在等待/使用该事件则不删除，后者则总是删除。
```
/*
*********************************************************************************************************
*                                        OS???Pend() OPTIONS
*
* These #defines are used to establish the options for OS???PendAbort().
*********************************************************************************************************
*/
#define  OS_PEND_OPT_NONE             0u    /* NO option selected                                      */
#define  OS_PEND_OPT_BROADCAST        1u    /* Broadcast action to ALL tasks waiting                   */

/*
*********************************************************************************************************
*                                     OS???PostOpt() OPTIONS
*
* These #defines are used to establish the options for OSMboxPostOpt() and OSQPostOpt().
*********************************************************************************************************
*/
#define  OS_POST_OPT_NONE          0x00u    /* NO option selected                                      */
#define  OS_POST_OPT_BROADCAST     0x01u    /* Broadcast message to ALL tasks waiting                  */
#define  OS_POST_OPT_FRONT         0x02u    /* Post to highest priority task waiting                   */
#define  OS_POST_OPT_NO_SCHED      0x04u 
```

事件相关宏定义。

```
#define  OS_TASK_OPT_NONE        0x0000u    /* 不使用 */
#define  OS_TASK_OPT_STK_CHK     0x0001u    /* 栈空间还剩下多少 */ 
#define  OS_TASK_OPT_STK_CLR     0x0002u    /* 清理栈 */
#define  OS_TASK_OPT_SAVE_FP     0x0004u    /* 保存浮点单元的寄存器 */
```

CM3内核不支持浮点单元的(CM4内核支持)。OS_TASK_OPT_SAVE_FP用于保存浮点指针(在进行上下文切换时)。
这几个宏在用于创建任务的函数OSTaskCreateExt()的参数使用。OSTaskCreate()是早期uCOS-II创建任务的函数，OSTaskCreateExt()则后期添加上的，也是用于创建任务。前者原型为：

`INT8U  OSTaskCreate (void (*task)(void *p_arg), void *p_arg, OS_STK *ptos, INT8U prio)`
后者的原型为：
```
INT8U  OSTaskCreateExt (void   (*task)(void *p_arg),
                        void    *p_arg,
                        OS_STK  *ptos,     /* top */
                        INT8U    prio,
                        INT16U   id,
                        OS_STK  *pbos,      /* button */
                        INT32U   stk_size,  /* 栈的大小 */
                        void    *pext,      /* 用户扩展数据 */
                        INT16U   opt)   
```
后者多了5个参数，其中opt参数取值为以上宏。

```
/*
*********************************************************************************************************
*                            TIMER OPTIONS (see OSTmrStart() and OSTmrStop())
*********************************************************************************************************
*/
#define  OS_TMR_OPT_NONE              0u    /* No option selected                                      */

#define  OS_TMR_OPT_ONE_SHOT          1u    /* Timer will not automatically restart when it expires    */
#define  OS_TMR_OPT_PERIODIC          2u    /* Timer will     automatically restart when it expires    */

#define  OS_TMR_OPT_CALLBACK          3u    /* OSTmrStop() option to call 'callback' w/ timer arg.     */
#define  OS_TMR_OPT_CALLBACK_ARG      4u    /* OSTmrStop() option to call 'callback' w/ new   arg.     */

/*
*********************************************************************************************************
*                                            TIMER STATES
*********************************************************************************************************
*/
#define  OS_TMR_STATE_UNUSED          0u
#define  OS_TMR_STATE_STOPPED         1u
#define  OS_TMR_STATE_COMPLETED       2u
#define  OS_TMR_STATE_RUNNING         3u
```

定时器相关的宏定义。
```
#define OS_ERR_NONE                   0u

#define OS_ERR_EVENT_TYPE             1u
#define OS_ERR_PEND_ISR               2u

...

#define OS_ERR_TMR_NAME_TOO_LONG    140u
#define OS_ERR_TMR_INVALID_STATE    141u
#define OS_ERR_TMR_STOPPED          142u
#define OS_ERR_TMR_NO_CALLBACK      143u
```

系统使用的错误码。
```
#define OS_NO_ERR                    OS_ERR_NONE
#define OS_TIMEOUT                   OS_ERR_TIMEOUT
//...
#define OS_FLAG_GRP_DEPLETED         OS_ERR_FLAG_GRP_DEPLETED
```
版本后小于2.84的系统使用的错误码。

2. 事件控制块OS_EVENT
```
#if (OS_EVENT_EN) && (OS_MAX_EVENTS > 0)
typedef struct os_event {
    INT8U    OSEventType;                    /* 指明何种类型的事件，取值见上面的OS_EVENT_TYPE_xxxx */
    void    *OSEventPtr;                     /* 指向事件的有效信息 */
    INT16U   OSEventCnt;                     /* 用于指明信号量的总数(信号量也是一种事件)。因为Mutex是一种特殊的信号量，
                                                其初始值为1，所以也支持此值 */
#if OS_LOWEST_PRIO <= 63
    INT8U    OSEventGrp;                     /* 事件表的组 */
    INT8U    OSEventTbl[OS_EVENT_TBL_SIZE];  /* 事件表。这两个参数类似于之前讲的任务就绪表 */
#else
    INT16U   OSEventGrp;                     /* Group corresponding to tasks waiting for event to occur */
    INT16U   OSEventTbl[OS_EVENT_TBL_SIZE];  /* List of tasks waiting for event to occur                */
#endif

#if OS_EVENT_NAME_SIZE > 1
    INT8U    OSEventName[OS_EVENT_NAME_SIZE]; /* 事件的名字 */
#endif
} OS_EVENT;
#endif
```

3. flag控制块相关
flag也属于事件(event)的一种，像Mutex、信号量和消息盒子等也属于event。由于flag的设计及使用与众不同，用OS_EVENT结构体无法表征，所以单独使用OS_FLAG_GRP结构体描述。
```
#if (OS_FLAG_EN > 0) && (OS_MAX_FLAGS > 0)
#if OS_FLAGS_NBITS == 8      /* Determine the size of OS_FLAGS (8, 16 or 32 bits) */
typedef  INT8U    OS_FLAGS;
#endif

#if OS_FLAGS_NBITS == 16
typedef  INT16U   OS_FLAGS;
#endif

#if OS_FLAGS_NBITS == 32
typedef  INT32U   OS_FLAGS;
#endif
```

系统中的flag是8位、16位、32位可选的。

```typedef struct os_flag_grp {                /* Event Flag Group */
    INT8U         OSFlagType;               /* 前只有OS_EVENT_TYPE_FLAG这种类型的flag */
    void         *OSFlagWaitList;           /* 指向flag链表的首节点 */
    OS_FLAGS      OSFlagFlags;              /* 要等待flag中的哪几个bit */  
#if OS_FLAG_NAME_SIZE > 1
    INT8U         OSFlagName[OS_FLAG_NAME_SIZE];
#endif
} OS_FLAG_GRP;

每个flag节点用OS_FLAG_NODE结构体描述：
typedef struct os_flag_node {  
    void         *OSFlagNodeNext;           /* Pointer to next     NODE in wait list */
    void         *OSFlagNodePrev;           /* Pointer to previous NODE in wait list */
    void         *OSFlagNodeTCB;            /* 正在排队等待flag的任务的TCB */
    void         *OSFlagNodeFlagGrp;        /* 指向flag所在的节点 */
    OS_FLAGS      OSFlagNodeFlags;          /* 要等待的flag的BIT几 */
    INT8U         OSFlagNodeWaitType;       /* 等待flag的等待类型。Type of wait: */
                                            /*      OS_FLAG_WAIT_AND */
                                            /*      OS_FLAG_WAIT_ALL */
                                            /*      OS_FLAG_WAIT_OR */
                                            /*      OS_FLAG_WAIT_ANY */
} OS_FLAG_NODE;
```

每个flag节点用双向链表的方式管理。

4. 消息盒子Mbox的数据描述结构体
```#if OS_MBOX_EN > 0
typedef struct os_mbox_data {
    void   *OSMsg;                   /* 指向数据的有效信息 */
#if OS_LOWEST_PRIO <= 63
    INT8U   OSEventTbl[OS_EVENT_TBL_SIZE]; /* List of tasks waiting for event to occur                 */
    INT8U   OSEventGrp;                    /* Group corresponding to tasks waiting for event to occur  */
#else
    INT16U  OSEventTbl[OS_EVENT_TBL_SIZE]; /* List of tasks waiting for event to occur                 */
    INT16U  OSEventGrp;                    /* Group corresponding to tasks waiting for event to occur  */
#endif
} OS_MBOX_DATA;
#endif
```

5. 动态内存的相关结构体
在c语言中动态分配内存使用malloc()和free()两个c库函数，它们是属于c库的内容，所以uCOS-II要支持这两个函数来实现动态内存分配，就要移植c库。对于运行RTOS的嵌入式软件来说，显得庞大。所以uCOS-II自定义了动态内存分配相关的函数。如下即为函数相关的描述结构体：

```#if (OS_MEM_EN > 0) && (OS_MAX_MEM_PART > 0)
typedef struct os_mem {                   /* MEMORY CONTROL BLOCK                                      */
    void   *OSMemAddr;                    /* Pointer to beginning of memory partition                  */
    void   *OSMemFreeList;                /* Pointer to list of free memory blocks                     */
    INT32U  OSMemBlkSize;                 /* Size (in bytes) of each block of memory                   */
    INT32U  OSMemNBlks;                   /* Total number of blocks in this partition                  */
    INT32U  OSMemNFree;                   /* Number of memory blocks remaining in this partition       */
#if OS_MEM_NAME_SIZE > 1
    INT8U   OSMemName[OS_MEM_NAME_SIZE];  /* Memory partition name                                     */
#endif
} OS_MEM;


typedef struct os_mem_data {
    void   *OSAddr;                    /* Pointer to the beginning address of the memory partition     */
    void   *OSFreeList;                /* Pointer to the beginning of the free list of memory blocks   */
    INT32U  OSBlkSize;                 /* Size (in bytes) of each memory block                         */
    INT32U  OSNBlks;                   /* Total number of blocks in the partition                      */
    INT32U  OSNFree;                   /* Number of memory blocks free                                 */
    INT32U  OSNUsed;                   /* Number of memory blocks used                                 */
} OS_MEM_DATA;
#endif
```

6. 互斥锁(Mutex)数据的描述结构体
```#if OS_MUTEX_EN > 0
typedef struct os_mutex_data {
#if OS_LOWEST_PRIO <= 63
    INT8U   OSEventTbl[OS_EVENT_TBL_SIZE];  /* List of tasks waiting for event to occur                */
    INT8U   OSEventGrp;                     /* Group corresponding to tasks waiting for event to occur */
#else
    INT16U  OSEventTbl[OS_EVENT_TBL_SIZE];  /* List of tasks waiting for event to occur                */
    INT16U  OSEventGrp;                     /* Group corresponding to tasks waiting for event to occur */
#endif
    BOOLEAN OSValue;                        /* Mutex value (OS_FALSE = used, OS_TRUE = available)      */
    INT8U   OSOwnerPrio;                    /* Mutex owner's task priority or 0xFF if no owner         */
    INT8U   OSMutexPIP;                     /* Priority Inheritance Priority or 0xFF if no owner       */
} OS_MUTEX_DATA;
#endif
```

7. 消息队列(Queue)控制块及数据描述结构体
队列相当于环形缓冲区，需要4个指针：分别指向头、指向尾指针、指向下一个数据要放入的位置、指向下一个要放出数据的位置。

```#if OS_Q_EN > 0
typedef struct os_q {    /* QUEUE CONTROL BLOCK                                         */
    struct os_q   *OSQPtr;              /* 指向下一个Queue */            
    void         **OSQStart;            /* Queue中的第一个元素 */
    void         **OSQEnd;              /* Queue中的最后一个元素 */
    void         **OSQIn;               /* Pointer to where next message will be inserted  in   the Q  */
    void         **OSQOut;              /* Pointer to where next message will be extracted from the Q  */
    INT16U         OSQSize;             /* Queue中元素的个数。单位是元素的个数，不是字节数 */
    INT16U         OSQEntries;          /* 当前队列用来存放数据的空间的内容用了多少 */  
} OS_Q;


typedef struct os_q_data {
    void          *OSMsg;             /* Queue的有效消息 */
    INT16U         OSNMsgs;           /* 有效消息的个数 */ 
    INT16U         OSQSize;           /* 数据总大小 */                                      */
#if OS_LOWEST_PRIO <= 63
    INT8U          OSEventTbl[OS_EVENT_TBL_SIZE];  /* List of tasks waiting for event to occur         */
    INT8U          OSEventGrp;          /* Group corresponding to tasks waiting for event to occur     */
#else
    INT16U         OSEventTbl[OS_EVENT_TBL_SIZE];  /* List of tasks waiting for event to occur         */
    INT16U         OSEventGrp;          /* Group corresponding to tasks waiting for event to occur     */
#endif
} OS_Q_DATA;
#endif
```

8. 信号量数据描述结构体
```#if OS_SEM_EN > 0
typedef struct os_sem_data {
    INT16U  OSCnt;          /* 信号量的当前值为多少 */ 

/* 等待信号量的任务任务队列。用到这个两个参数说明OSCnt为零了，不然不会有等待任务的 */    
#if OS_LOWEST_PRIO <= 63
    INT8U   OSEventTbl[OS_EVENT_TBL_SIZE];   /* List of tasks waiting for event to occur                */
    INT8U   OSEventGrp;                     /* Group corresponding to tasks waiting for event to occur */
#else
    INT16U  OSEventTbl[OS_EVENT_TBL_SIZE];  /* List of tasks waiting for event to occur                */
    INT16U  OSEventGrp;                     /* Group corresponding to tasks waiting for event to occur */
#endif
} OS_SEM_DATA;
#endif
```

9. 任务栈信息
```#if OS_TASK_CREATE_EXT_EN > 0
typedef struct os_stk_data {
    INT32U  OSFree;                    /* 还剩下多少栈空间 */
    INT32U  OSUsed;                    /* 已经使用了多少栈空间 */
} OS_STK_DATA;
#endif
```

10. 任务控制块TCB
后面详细说明.

11. 定时器相关
```#if OS_TMR_EN > 0
typedef  void (*OS_TMR_CALLBACK)(void *ptmr, void *parg);
typedef  struct  os_tmr {
    INT8U            OSTmrType;                       /* Should be set to OS_TMR_TYPE */
    OS_TMR_CALLBACK  OSTmrCallback;                   /* Function to call when timer expires */
    void            *OSTmrCallbackArg;                /* Argument to pass to function when timer expires */
    void            *OSTmrNext;                       /* Double link list pointers */
    void            *OSTmrPrev;
    INT32U           OSTmrMatch;                      /* Timer expires when OSTmrTime == OSTmrMatch */
    INT32U           OSTmrDly;                        /* Delay time before periodic update starts */
    INT32U           OSTmrPeriod;                     /* Period to repeat timer */
#if OS_TMR_CFG_NAME_SIZE > 0
    INT8U            OSTmrName[OS_TMR_CFG_NAME_SIZE]; /* Name to give the timer  */
#endif
    INT8U            OSTmrOpt;                        /* Options (see OS_TMR_OPT_xxx) */
    INT8U            OSTmrState;                      /* Indicates the state of the timer: */
                                                      /*     OS_TMR_STATE_UNUSED */
                                                      /*     OS_TMR_STATE_RUNNING */
                                                      /*     OS_TMR_STATE_STOPPED */
} OS_TMR;

typedef  struct  os_tmr_wheel {
    OS_TMR          *OSTmrFirst;                      /* Pointer to first timer in linked list                         */
    INT16U           OSTmrEntries;
} OS_TMR_WHEEL;
#endif
```

12. 系统全局变量的定义
```OS_EXT  INT32U OSCtxSwCtr; /* 任务切换的次数 */

#if (OS_EVENT_EN) && (OS_MAX_EVENTS > 0)
OS_EXT  OS_EVENT         *OSEventFreeList;          /* 指向event链表的空闲节点 */
OS_EXT  OS_EVENT          OSEventTbl[OS_MAX_EVENTS];/* 全局event数组 */
#endif

#if (OS_FLAG_EN > 0) && (OS_MAX_FLAGS > 0)
OS_EXT  OS_FLAG_GRP       OSFlagTbl[OS_MAX_FLAGS];  /* 全局flag数组*/
OS_EXT  OS_FLAG_GRP      *OSFlagFreeList;           /* 指向flag链表的空闲节点 */
#endif

#if OS_TASK_STAT_EN > 0
OS_EXT  INT8U             OSCPUUsage;               /* cpu使用率 */
OS_EXT  INT32U            OSIdleCtrMax;             /* 1s内空闲计数最大值，cpu在没事做的时候计的数 */

OS_EXT  INT32U            OSIdleCtrRun;             /* 1s内空闲计数器计数了多少。1s内可能含有空闲任务和非空闲任务，这个值用于记录空闲的。*/

OS_EXT  BOOLEAN           OSStatRdy;                /* 标志标量指示统计任务是否准备好*/

OS_EXT  OS_STK            OSTaskStatStk[OS_TASK_STAT_STK_SIZE];      /* 统计任务的任务栈 */
#endif

OS_EXT  INT8U             OSIntNesting;             /* 中断的嵌套级别 */
OS_EXT  INT8U             OSLockNesting;            /* 多任务锁的嵌套级别 */
OS_EXT  INT8U             OSPrioCur;                /* 当前正在运行的任务的优先级 */
OS_EXT  INT8U             OSPrioHighRdy;            /* 当前处于就绪态的任务中优先级最高的优先级 */

#if OS_LOWEST_PRIO <= 63
OS_EXT  INT8U             OSRdyGrp;                        /* 就绪组 */
OS_EXT  INT8U             OSRdyTbl[OS_RDY_TBL_SIZE];       /* 就绪表 */
#else
OS_EXT  INT16U            OSRdyGrp; 
OS_EXT  INT16U            OSRdyTbl[OS_RDY_TBL_SIZE]; 
#endif

OS_EXT  BOOLEAN           OSRunning;                /* 表示os启动尚未完成初始化时候为0 */
OS_EXT  INT8U             OSTaskCtr;                /* 当前一共创建了几个任务 */
OS_EXT  volatile  INT32U  OSIdleCtr;                /* 空闲计数器。跟统计任务计算cpu空闲使用率等相关 */
OS_EXT  OS_STK            OSTaskIdleStk[OS_TASK_IDLE_STK_SIZE];      /* 空闲任务栈 */

OS_EXT  OS_TCB           *OSTCBCur;                 /* 指向当前正在执行的任务TCB */
OS_EXT  OS_TCB           *OSTCBFreeList;            /* 这个全局变量作为链表头指针，指向uc/OS维护的TCB双向链表。uCOS-II */
                                                    /* 中每个任务都有一个TCB，这些TCB是通过内置的TCB结构体中的2个指针
                                                    /* (OSTCBNext、OSTCBPrev)构建了双向链表这样我们整个uC/OS中所有的代码在 */
                                                    /* 任何位置都可以通过访问全局变量OSTCBList来找到所有任务的TCB */

OS_EXT  OS_TCB           *OSTCBPrioTbl[OS_LOWEST_PRIO + 1];
OS_EXT  OS_TCB            OSTCBTbl[OS_MAX_TASKS + OS_N_SYS_TASKS];  /* 系统中事先定义好的所有任务的TCB数组 */
                                                                    /* OS_N_SYS_TASKS指系统创建的任务数 */

#if OS_TICK_STEP_EN > 0
OS_EXT  INT8U             OSTickStepState;          /* os view相关，不重要 */
#endif

#if (OS_MEM_EN > 0) && (OS_MAX_MEM_PART > 0)
OS_EXT  OS_MEM           *OSMemFreeList;                /* 动态内存管理相关  */
OS_EXT  OS_MEM            OSMemTbl[OS_MAX_MEM_PART];    /* Storage for memory partition manager            */
#endif

#if (OS_Q_EN > 0) && (OS_MAX_QS > 0)
OS_EXT  OS_Q             *OSQFreeList;              /* Pointer to list of free QUEUE control blocks    */
OS_EXT  OS_Q              OSQTbl[OS_MAX_QS];        /* 支持4个Queue */
#endif

#if OS_TIME_GET_SET_EN > 0
OS_EXT  volatile  INT32U  OSTime;                   /* 系统当前时间记录，以tick单位来记录 */
#endif

#if OS_TMR_EN > 0
//定时器相关
OS_EXT  INT16U            OSTmrFree;                /* Number of free entries in the timer pool        */
OS_EXT  INT16U            OSTmrUsed;                /* Number of timers used                           */
OS_EXT  INT32U            OSTmrTime;                /* Current timer time                              */

OS_EXT  OS_EVENT         *OSTmrSem;                 /* Sem. used to gain exclusive access to timers    */
OS_EXT  OS_EVENT         *OSTmrSemSignal;           /* Sem. used to signal the update of timers        */

OS_EXT  OS_TMR            OSTmrTbl[OS_TMR_CFG_MAX]; /* Table containing pool of timers                 */
OS_EXT  OS_TMR           *OSTmrFreeList;            /* Pointer to free list of timers                  */
OS_EXT  OS_STK            OSTmrTaskStk[OS_TASK_TMR_STK_SIZE];

OS_EXT  OS_TMR_WHEEL      OSTmrWheelTbl[OS_TMR_CFG_WHEEL_SIZE];
#endif

extern  INT8U   const     OSUnMapTbl[256];          /* 常数数组，跟计算当前的最高优先级的任务有关 */

```
接下来,详细阐述uCOS的任务机制

完了就是uCOS-II的核心函数的声明。ucos_ii.h文件就粗略阅读到这里,主要完成了对于整个系统的构建和定义.
