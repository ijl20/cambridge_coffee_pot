
import asyncio

class Watchdog():
    """
    Watchdog - will poll the .watchdog method of the watched coroutine

    Instantiation by SensorNode:
        watchdog = WatchDog(settings=settings, watched=<watched coro>, period=30) # period in seconds

    Methods:
        watchdog.start()
    """

    def __init__(self, settings=None, watched=None, period=60):
        print("Watchdog() __init__ {} seconds".format(period))

        self.settings = settings
        self.period = period
        self.watched = watched

        self.quit = False
        self.finish_event = asyncio.Event()

    # start() method is async with permanent loop, using asyncio.sleep().
    async def start(self):
        self.quit = False
        while not self.quit:
            await self.watched.watchdog()
            sleep_task = asyncio.ensure_future(asyncio.sleep(self.period))
            finish_task = asyncio.ensure_future(self.finish_event.wait())

            finished, pending = await asyncio.wait( [ sleep_task, finish_task ],
                                                    return_when=asyncio.FIRST_COMPLETED )

        print("Watchdog finished")

    async def finish(self):
        self.quit = True
        print("Watchdog set to finish")

        self.finish_event.set()

        print("Watchdog finish completed")

