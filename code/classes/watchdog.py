
import asyncio

class Watchdog():
    """
    Watchdog - will poll the .watchdog method of the watched coroutine

    Instantiation:
        watchdog = WatchDog(settings=settings, watched=<watched coro>, period=30) # period in seconds

    Methods:
        watchdog.start()
    """

    def __init__(self, settings=None, watched=None, period=60):
        print("Watchdog() __init__ {} seconds".format(period))

        self.settings = settings
        self.period = period
        self.watched = watched

    # start() method is async with permanent loop, using asyncio.sleep().
    async def start(self):
        self.quit = False
        while not self.quit:
            await self.watched.watchdog()
            await asyncio.sleep(self.period)

    async def finish(self):
        #debug this won't terminate the start() loop until 'period' expires
        self.quit = True
        print("watchdog finish(): set to quit")

